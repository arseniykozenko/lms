import React from "react";
import {
  BellOutlined,
  BookOutlined,
  DownOutlined,
  DeleteOutlined,
  ExclamationCircleOutlined,
  IdcardOutlined,
  LogoutOutlined,
  MenuOutlined,
  MessageOutlined,
  MoonOutlined,
  ReadOutlined,
  RiseOutlined,
  SunOutlined,
  UserOutlined,
} from "@ant-design/icons";
import {
  Avatar,
  Badge,
  Button,
  Card,
  Descriptions,
  Divider,
  Dropdown,
  Drawer,
  Empty,
  Layout,
  List,
  Menu,
  Popconfirm,
  Popover,
  Segmented,
  Space,
  Switch,
  Tag,
  Typography,
  notification,
} from "antd";
import { useUnit } from "effector-react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { createChatWebSocket } from "../api/chat";
import { getUserDisplayName } from "../lib/userName";
import { $user, signOutClicked } from "../models/auth";
import {
  $notifications,
  $notificationsUnreadCount,
  deleteNotificationFx,
  deleteReadNotificationsFx,
  markAllNotificationsReadFx,
  markNotificationReadFx,
  notificationsRefreshRequested,
} from "../models/notifications";
import { useThemeMode } from "../theme/ThemeProvider";

const { Header, Content, Sider } = Layout;
const NOTIFICATIONS_REFRESH_MS = 60000;
const STORAGE_KEY = "lms-auth";

const NOTIFICATION_GROUPS = {
  comment_reply: "learning",
  chat_message: "learning",
  assignment_submitted: "learning",
  assignment_published: "learning",
  quiz_published: "learning",
  assignment_graded: "feedback",
  assignment_feedback: "feedback",
  teacher_announcement: "feedback",
  deadline_soon: "deadlines",
  deadline_overdue: "deadlines",
  deadline_changed: "deadlines",
  performance_risk: "risks",
};
const TOASTABLE_NOTIFICATION_TYPES = new Set([
  "teacher_announcement",
  "deadline_soon",
  "deadline_overdue",
  "deadline_changed",
  "performance_risk",
  "assignment_graded",
  "assignment_feedback",
]);

export function AppShell({ children, title, subtitle }) {
  const location = useLocation();
  const navigate = useNavigate();
  const [toastApi, toastContextHolder] = notification.useNotification();

  const [user, notifications, unreadCount, logout, refreshNotifications, markNotificationRead, markAllNotificationsRead, removeNotification, removeReadNotifications] =
    useUnit([
      $user,
      $notifications,
      $notificationsUnreadCount,
      signOutClicked,
      notificationsRefreshRequested,
      markNotificationReadFx,
      markAllNotificationsReadFx,
      deleteNotificationFx,
      deleteReadNotificationsFx,
    ]);

  const [mobileOpen, setMobileOpen] = React.useState(false);
  const [notificationsOpen, setNotificationsOpen] = React.useState(false);
  const [notificationFilter, setNotificationFilter] = React.useState("all");
  const { mode: themeMode, toggleMode } = useThemeMode();
  const isAuthenticated = Boolean(user?.id);

  const announcedIdsRef = React.useRef(new Set());
  const announcedNotificationIdsRef = React.useRef(new Set());
  const wsRef = React.useRef(null);

  const roleTone =
    user?.role === "teacher"
      ? { color: "gold", label: "Преподаватель" }
      : user?.role === "admin"
        ? { color: "red", label: "Администратор" }
        : { color: "cyan", label: "Студент" };

  const menuItems = [
    { key: "/courses", icon: <BookOutlined />, label: <Link to="/courses">Каталог курсов</Link> },
    ...(isAuthenticated ? [{ key: "/dashboard", icon: <ReadOutlined />, label: <Link to="/dashboard">Главная</Link> }] : []),
    ...(isAuthenticated ? [{ key: "/my-courses", icon: <BookOutlined />, label: <Link to="/my-courses">Мои курсы</Link> }] : []),
  ];

  if (isAuthenticated) {
    menuItems.splice(3, 0, {
      key: "/chat",
      icon: <MessageOutlined />,
      label: <Link to="/chat">Чат</Link>,
    });
  }

  if (isAuthenticated && user?.role === "admin") {
    menuItems.splice(4, 0, {
      key: "/moderation",
      icon: <ExclamationCircleOutlined />,
      label: <Link to="/moderation">Модерация</Link>,
    });
  }

  React.useEffect(() => {
    if (!isAuthenticated) return undefined;
    if (!user?.id) return undefined;

    const refresh = () => {
      if (document.visibilityState === "visible") refreshNotifications();
    };

    refresh();
    const intervalId = window.setInterval(refresh, NOTIFICATIONS_REFRESH_MS);
    window.addEventListener("focus", refresh);
    document.addEventListener("visibilitychange", refresh);

    return () => {
      window.clearInterval(intervalId);
      window.removeEventListener("focus", refresh);
      document.removeEventListener("visibilitychange", refresh);
    };
  }, [isAuthenticated, refreshNotifications, user?.id]);

  React.useEffect(() => {
    if (!isAuthenticated) return;
    const now = Date.now();
    notifications.forEach((item) => {
      if (!item?.id) return;
      if (!TOASTABLE_NOTIFICATION_TYPES.has(item.type)) return;
      if (announcedNotificationIdsRef.current.has(item.id)) return;
      announcedNotificationIdsRef.current.add(item.id);
      const createdAt = new Date(item.created_at || 0).getTime();
      if (Number.isNaN(createdAt) || now - createdAt > 1000 * 60 * 5) return;

      toastApi.open({
        key: `notif-${item.id}`,
        message: item.title || "Новое уведомление",
        description: item.message,
        duration: 6,
        placement: "topRight",
        icon: getNotificationToastIcon(item.type),
        onClick: () => {
          const nextLink = resolveNotificationLink(item, user);
          if (nextLink) navigate(nextLink);
          setNotificationsOpen(false);
        },
      });
    });
  }, [isAuthenticated, navigate, notifications, toastApi, user]);

  React.useEffect(() => {
    if (!isAuthenticated) return undefined;
    if (!user?.id) return undefined;
    let closed = false;
    let opened = false;
    const token = readStoredToken();
    if (!token) return undefined;

    const ws = createChatWebSocket(token);
    wsRef.current = ws;

    ws.onopen = () => {
      opened = true;
    };
    ws.onmessage = (event) => {
      const payload = JSON.parse(event.data || "{}");
      if (payload.type !== "chat.message" || !payload.message) return;
      const msg = payload.message;
      if (msg.recipient_id !== user.id) return;
      const toastKey = `chat-ws-${msg.id}`;
      if (announcedIdsRef.current.has(toastKey)) return;
      announcedIdsRef.current.add(toastKey);
      toastApi.open({
        key: toastKey,
        message: "Новое сообщение",
        description: msg.content,
        duration: 5,
        placement: "topRight",
        icon: <MessageOutlined style={{ color: "#1677ff" }} />,
        onClick: () => {
          navigate(`/chat?partner=${msg.sender_id}`);
        },
      });
      refreshNotifications();
    };
    ws.onerror = () => {
      if (!closed && opened) {
        // silent fallback to polling notifications
      }
    };

    return () => {
      closed = true;
      try {
        ws.close();
      } catch {
        // ignore
      }
      wsRef.current = null;
    };
  }, [isAuthenticated, navigate, refreshNotifications, toastApi, user?.id]);

  const filteredNotifications = notifications.filter((item) => {
    if (notificationFilter === "all") return true;
    if (notificationFilter === "unread") return !item.is_read;
    return NOTIFICATION_GROUPS[item.type] === notificationFilter;
  });
  const hasReadNotifications = notifications.some((item) => item.is_read);

  const profileDropdown = (
    <Card className="profile-dropdown-card" size="small" styles={{ body: { padding: 14 } }}>
      <Space direction="vertical" size={10} style={{ width: "100%" }}>
        <Space align="start" size={10}>
          <Avatar size={40} icon={<UserOutlined />} src={user?.profile_photo_url || undefined} />
          <Space direction="vertical" size={0}>
            <Typography.Text strong>{getUserDisplayName(user)}</Typography.Text>
            <Typography.Text type="secondary">{user?.email || "—"}</Typography.Text>
          </Space>
        </Space>
        <Descriptions
          size="small"
          column={1}
          items={[
            {
              key: "role",
              label: "Роль",
              children: (
                <Tag color={roleTone.color} style={{ marginInlineEnd: 0 }}>
                  {roleTone.label}
                </Tag>
              ),
            },
          ]}
        />
        <Divider style={{ margin: "4px 0" }} />
        <Space direction="vertical" size={6} style={{ width: "100%" }}>
          <Button block icon={<IdcardOutlined />} onClick={() => navigate("/profile")}>
            Профиль
          </Button>
          <Button
            block
            danger
            icon={<LogoutOutlined />}
            onClick={() => {
              logout();
              navigate("/login");
            }}
          >
            Выйти
          </Button>
        </Space>
      </Space>
    </Card>
  );

  const notificationContent = (
    <Card className="notifications-dropdown-card" size="small" styles={{ body: { padding: 12 } }}>
      <Space direction="vertical" size={12} style={{ width: "100%" }}>
        <div className="notifications-head">
          <Typography.Text strong>Уведомления</Typography.Text>
          <Space size={4}>
            <Button type="link" size="small" disabled={!unreadCount} onClick={() => markAllNotificationsRead()}>
              Прочитать все
            </Button>
            <Popconfirm
              title="Удалить все прочитанные?"
              okText="Удалить"
              cancelText="Отмена"
              onConfirm={() => removeReadNotifications()}
            >
              <Button type="link" size="small" danger disabled={!hasReadNotifications}>
                Удалить прочитанные
              </Button>
            </Popconfirm>
          </Space>
        </div>

        <Segmented
          size="small"
          block
          value={notificationFilter}
          onChange={setNotificationFilter}
          options={[
            { label: "Все", value: "all" },
            { label: "Непрочит.", value: "unread" },
            { label: "Учеба", value: "learning" },
            { label: "Дедлайны", value: "deadlines" },
            { label: "Риски", value: "risks" },
          ]}
        />

        {filteredNotifications.length ? (
          <List
            className="notifications-list"
            dataSource={filteredNotifications}
            renderItem={(item) => (
              <List.Item
                className={`notifications-item ${item.is_read ? "" : "notifications-item-unread"}`}
                actions={[
                  <Button
                    key="delete"
                    type="text"
                    size="small"
                    icon={<DeleteOutlined />}
                    onClick={async (event) => {
                      event.preventDefault();
                      event.stopPropagation();
                      await removeNotification(item.id);
                    }}
                  />,
                ]}
                onClick={async () => {
                  if (!item.is_read) await markNotificationRead(item.id);
                  const nextLink = resolveNotificationLink(item, user);
                  if (nextLink) {
                    navigate(nextLink);
                    setNotificationsOpen(false);
                  }
                }}
              >
                <List.Item.Meta
                  title={
                    <Space wrap>
                      <Typography.Text strong>{item.title}</Typography.Text>
                      <Tag color={getNotificationTypeColor(item.type)} bordered={false}>
                        {getNotificationTypeLabel(item.type)}
                      </Tag>
                      {!item.is_read ? <Badge status="processing" /> : null}
                    </Space>
                  }
                  description={
                    <Space direction="vertical" size={2}>
                      <Typography.Text>{item.message}</Typography.Text>
                      <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                        {new Date(item.created_at).toLocaleString("ru-RU")}
                      </Typography.Text>
                    </Space>
                  }
                />
              </List.Item>
            )}
          />
        ) : (
          <Empty description="По выбранному фильтру уведомлений нет" image={Empty.PRESENTED_IMAGE_SIMPLE} />
        )}
      </Space>
    </Card>
  );

  return (
    <Layout className="screen-shell app-shell-layout">
      {toastContextHolder}

      <Sider breakpoint="lg" collapsedWidth="0" theme="light" className="glass-sider desktop-sider">
        <SidebarContent menuItems={menuItems} selectedKey={location.pathname} />
      </Sider>

      <Drawer
        title="Навигация"
        placement="left"
        onClose={() => setMobileOpen(false)}
        open={mobileOpen}
        width={280}
        className="mobile-shell-drawer"
      >
        <SidebarContent menuItems={menuItems} selectedKey={location.pathname} onNavigate={() => setMobileOpen(false)} />
      </Drawer>

      <Layout>
        <Header className="app-header">
          <div className="header-intro">
            <Button className="mobile-menu-button" icon={<MenuOutlined />} onClick={() => setMobileOpen(true)}>
              Меню
            </Button>
            <div>
              <Typography.Title level={2} className="page-title">
                {title}
              </Typography.Title>
              <Typography.Text className="page-subtitle">{subtitle}</Typography.Text>
            </div>
          </div>

          <div className="header-actions">
            <Switch
              className="theme-switch"
              checked={themeMode === "dark"}
              checkedChildren={<MoonOutlined />}
              unCheckedChildren={<SunOutlined />}
              onChange={toggleMode}
            />

            {isAuthenticated ? (
              <>
                <Popover
                  content={notificationContent}
                  trigger="click"
                  open={notificationsOpen}
                  onOpenChange={setNotificationsOpen}
                  placement="bottomRight"
                >
                  <Badge count={unreadCount} size="small">
                    <Button icon={<BellOutlined />} />
                  </Badge>
                </Popover>

                <Dropdown trigger={["click"]} placement="bottomRight" dropdownRender={() => profileDropdown}>
                  <button type="button" className="header-user header-user-trigger">
                    <Avatar size={42} icon={<UserOutlined />} src={user?.profile_photo_url || undefined} />
                    <div className="header-user-text">
                      <Typography.Text strong>{getUserDisplayName(user)}</Typography.Text>
                      <div className="header-user-meta">{user?.email}</div>
                    </div>
                    <DownOutlined className="header-user-chevron" />
                  </button>
                </Dropdown>
              </>
            ) : (
              <Space>
                <Button onClick={() => navigate("/login")}>Войти</Button>
                <Button type="primary" onClick={() => navigate("/register")}>
                  Регистрация
                </Button>
              </Space>
            )}
          </div>
        </Header>

        <Content className="app-content">{children}</Content>
      </Layout>
    </Layout>
  );
}

function resolveNotificationLink(item, user) {
  const rawLink = item?.link_url;
  if (!rawLink) return null;

  if (item?.type === "performance_risk" && user?.role === "student") {
    const match = rawLink.match(/^\/courses\/([a-f0-9-]+)\/progress$/i);
    if (match?.[1]) {
      return `/courses/${match[1]}`;
    }
  }

  return rawLink;
}

function readStoredToken() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw)?.token || null : null;
  } catch {
    return null;
  }
}


function SidebarContent({ menuItems, selectedKey, onNavigate }) {
  return (
    <>
      <div className="brand-block">
        <div className="brand-orb">L</div>
        <div>
          <Typography.Title level={4} className="brand-title">
            EdFlow
          </Typography.Title>
          <Typography.Text className="brand-subtitle">Цифровая образовательная платформа</Typography.Text>
        </div>
      </div>

      <Menu mode="inline" selectedKeys={[selectedKey]} items={menuItems} onClick={onNavigate} />

      <div className="sider-footer">
        <Typography.Text type="secondary">Курсы, коммуникация и аналитика в едином рабочем контуре.</Typography.Text>
      </div>
    </>
  );
}

function getNotificationTypeLabel(type) {
  switch (type) {
    case "assignment_feedback":
      return "Фидбек";
    case "assignment_published":
      return "Задание";
    case "quiz_published":
      return "Тест";
    case "deadline_changed":
      return "Срок";
    case "deadline_soon":
      return "Скоро";
    case "deadline_overdue":
      return "Просрочено";
    case "teacher_announcement":
      return "Объявление";
    case "performance_risk":
      return "Риск";
    case "comment_reply":
      return "Ответ";
    case "chat_message":
      return "Сообщение";
    case "assignment_submitted":
      return "Сдача";
    case "assignment_graded":
      return "Оценка";
    default:
      return "LMS";
  }
}

function getNotificationTypeColor(type) {
  switch (NOTIFICATION_GROUPS[type]) {
    case "deadlines":
      return "orange";
    case "risks":
      return "red";
    case "feedback":
      return "purple";
    default:
      return "blue";
  }
}

function getNotificationToastIcon(type) {
  if (NOTIFICATION_GROUPS[type] === "risks") {
    return <ExclamationCircleOutlined style={{ color: "#ff4d4f" }} />;
  }
  if (NOTIFICATION_GROUPS[type] === "deadlines") {
    return <BellOutlined style={{ color: "#fa8c16" }} />;
  }
  return <RiseOutlined style={{ color: "#1677ff" }} />;
}
