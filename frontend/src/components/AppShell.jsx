import React from "react";
import {
  BookOutlined,
  IdcardOutlined,
  LogoutOutlined,
  MenuOutlined,
  ReadOutlined,
  UserOutlined,
} from "@ant-design/icons";
import { Avatar, Button, Drawer, Layout, Menu, Tag, Typography } from "antd";
import { useUnit } from "effector-react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { $user, signOutClicked } from "../models/auth";

const { Header, Content, Sider } = Layout;

export function AppShell({ children, title, subtitle }) {
  const location = useLocation();
  const navigate = useNavigate();
  const user = useUnit($user);
  const logout = useUnit(signOutClicked);
  const [mobileOpen, setMobileOpen] = React.useState(false);

  const roleTone =
    user?.role === "teacher"
      ? { color: "gold", label: "Преподаватель" }
      : user?.role === "admin"
        ? { color: "red", label: "Администратор" }
        : { color: "cyan", label: "Студент" };

  const menuItems = [
    { key: "/dashboard", icon: <ReadOutlined />, label: <Link to="/dashboard">Главная</Link> },
    { key: "/courses", icon: <BookOutlined />, label: <Link to="/courses">Каталог курсов</Link> },
    { key: "/my-courses", icon: <BookOutlined />, label: <Link to="/my-courses">Мои курсы</Link> },
    { key: "/profile", icon: <IdcardOutlined />, label: <Link to="/profile">Профиль</Link> },
  ];

  return (
    <Layout className="screen-shell app-shell-layout">
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
            <Tag color={roleTone.color}>{roleTone.label}</Tag>
            <div className="header-user">
              <Avatar size={44} icon={<UserOutlined />} src={user?.profile_photo_url || undefined} />
              <div className="header-user-text">
                <Typography.Text strong>{user?.full_name || user?.email || "Пользователь"}</Typography.Text>
                <div className="header-user-meta">{user?.email}</div>
              </div>
            </div>
            <Button
              icon={<LogoutOutlined />}
              onClick={() => {
                logout();
                navigate("/login");
              }}
            >
              Выйти
            </Button>
          </div>
        </Header>

        <Content className="app-content">{children}</Content>
      </Layout>
    </Layout>
  );
}

function SidebarContent({ menuItems, selectedKey, onNavigate }) {
  return (
    <>
      <div className="brand-block">
        <div className="brand-orb">L</div>
        <div>
          <Typography.Title level={4} className="brand-title">
            Платформа LMS
          </Typography.Title>
          <Typography.Text className="brand-subtitle">Современное пространство обучения</Typography.Text>
        </div>
      </div>

      <Menu mode="inline" selectedKeys={[selectedKey]} items={menuItems} onClick={onNavigate} />

      <div className="sider-footer">
        <Typography.Text type="secondary">Учеба в структурированном и спокойном интерфейсе.</Typography.Text>
      </div>
    </>
  );
}
