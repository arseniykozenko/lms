import React from "react";
import { Alert, Button, Card, Col, DatePicker, Input, List, Popconfirm, Row, Segmented, Select, Space, Tag, Typography, message } from "antd";
import { useUnit } from "effector-react";
import dayjs from "dayjs";

import { blockUserByAdmin, listAdminAuditLogs, listAdminUsers, setUserRoleByAdmin, unblockUserByAdmin } from "../api/adminUsers";
import { hideCommentByAdmin, hideCourseByAdmin, listReports, restoreCommentByAdmin, restoreCourseByAdmin, reviewReport } from "../api/moderation";
import { AppShell } from "../components/AppShell";
import { getUserDisplayName } from "../lib/userName";
import { $user } from "../models/auth";

const STATUS_OPTIONS = [
  { value: "all", label: "Все" },
  { value: "open", label: "Открытые" },
  { value: "in_review", label: "На проверке" },
  { value: "resolved", label: "Решенные" },
  { value: "rejected", label: "Отклоненные" },
];

function statusLabel(value) {
  if (value === "open") return "Открыт";
  if (value === "in_review") return "На проверке";
  if (value === "resolved") return "Решен";
  if (value === "rejected") return "Отклонен";
  return value;
}

function targetLabel(value) {
  if (value === "course") return "Курс";
  if (value === "comment") return "Комментарий";
  if (value === "module_content") return "Материал";
  if (value === "chat_message") return "Сообщение в чате";
  return value;
}

export function ModerationPage() {
  const [user] = useUnit([$user]);

  const [statusFilter, setStatusFilter] = React.useState("open");
  const [items, setItems] = React.useState([]);
  const [users, setUsers] = React.useState([]);
  const [loading, setLoading] = React.useState(false);
  const [usersLoading, setUsersLoading] = React.useState(false);
  const [auditLoading, setAuditLoading] = React.useState(false);
  const [blockReason, setBlockReason] = React.useState("");
  const [blockUntil, setBlockUntil] = React.useState(null);
  const [auditItems, setAuditItems] = React.useState([]);
  const [auditActionFilter, setAuditActionFilter] = React.useState("all");
  const [reportActionPending, setReportActionPending] = React.useState({});
  const [targetState, setTargetState] = React.useState({});

  const isAdmin = user?.role === "admin";

  const load = React.useCallback(async () => {
    if (!isAdmin) return;
    setLoading(true);
    try {
      const data = await listReports(statusFilter === "all" ? undefined : statusFilter);
      setItems(data);
    } catch (error) {
      message.error(error?.response?.data?.detail || "Не удалось загрузить репорты");
    } finally {
      setLoading(false);
    }
  }, [isAdmin, statusFilter]);

  const loadUsers = React.useCallback(async () => {
    if (!isAdmin) return;
    setUsersLoading(true);
    try {
      setUsers(await listAdminUsers());
    } catch (error) {
      message.error(error?.response?.data?.detail || "Не удалось загрузить пользователей");
    } finally {
      setUsersLoading(false);
    }
  }, [isAdmin]);

  const loadAudit = React.useCallback(async () => {
    if (!isAdmin) return;
    setAuditLoading(true);
    try {
      setAuditItems(await listAdminAuditLogs(200));
    } catch (error) {
      message.error(error?.response?.data?.detail || "Не удалось загрузить аудит-лог");
    } finally {
      setAuditLoading(false);
    }
  }, [isAdmin]);

  React.useEffect(() => {
    load();
  }, [load]);

  React.useEffect(() => {
    loadUsers();
  }, [loadUsers]);

  React.useEffect(() => {
    loadAudit();
  }, [loadAudit]);

  async function updateStatus(reportId, status) {
    const pendingKey = `status:${reportId}:${status}`;
    setReportActionPending((prev) => ({ ...prev, [pendingKey]: true }));
    try {
      await reviewReport(reportId, { status });
      setItems((prev) => prev.map((item) => (item.id === reportId ? { ...item, status } : item)));

      if (status === "resolved" || status === "rejected") {
        message.success("Репорт перенесен в закрытые");
      } else {
        message.success("Статус репорта обновлен");
      }

      await loadAudit();
      await load();
    } catch (error) {
      message.error(error?.response?.data?.detail || "Не удалось обновить статус");
    } finally {
      setReportActionPending((prev) => {
        const next = { ...prev };
        delete next[pendingKey];
        return next;
      });
    }
  }

  async function runTargetAction(item, action) {
    const targetId = item.target_type === "course" ? item.course_id : item.comment_id;
    if (!targetId) return;
    const pendingKey = `target:${item.id}:${action}`;
    setReportActionPending((prev) => ({ ...prev, [pendingKey]: true }));
    try {
      if (item.target_type === "course") {
        if (action === "hide") await hideCourseByAdmin(item.course_id);
        if (action === "restore") await restoreCourseByAdmin(item.course_id);
      }
      if (item.target_type === "comment") {
        if (action === "hide") await hideCommentByAdmin(item.comment_id);
        if (action === "restore") await restoreCommentByAdmin(item.comment_id);
      }
      setTargetState((prev) => ({
        ...prev,
        [item.id]: {
          state: action === "hide" ? "hidden" : "restored",
          updatedAt: Date.now(),
        },
      }));
      message.success(action === "hide" ? "Объект скрыт модератором" : "Объект восстановлен");
      await loadAudit();
    } catch (error) {
      message.error(error?.response?.data?.detail || "Не удалось выполнить действие");
    } finally {
      setReportActionPending((prev) => {
        const next = { ...prev };
        delete next[pendingKey];
        return next;
      });
    }
  }

  async function changeRole(userId, role) {
    try {
      await setUserRoleByAdmin(userId, role);
      message.success("Роль обновлена");
      await loadUsers();
      await loadAudit();
    } catch (error) {
      message.error(error?.response?.data?.detail || "Не удалось изменить роль");
    }
  }

  async function blockUser(userId, permanent = false) {
    try {
      await blockUserByAdmin(userId, {
        blocked_reason: blockReason || "Нарушение правил платформы",
        blocked_until: permanent || !blockUntil ? null : blockUntil.toISOString(),
      });
      message.success("Пользователь заблокирован");
      await loadUsers();
      await loadAudit();
    } catch (error) {
      message.error(error?.response?.data?.detail || "Не удалось заблокировать пользователя");
    }
  }

  async function unblockUser(userId) {
    try {
      await unblockUserByAdmin(userId);
      message.success("Пользователь разблокирован");
      await loadUsers();
      await loadAudit();
    } catch (error) {
      message.error(error?.response?.data?.detail || "Не удалось разблокировать пользователя");
    }
  }

  const auditActions = React.useMemo(() => {
    const map = new Map();
    auditItems.forEach((item) => {
      if (!map.has(item.action)) {
        map.set(item.action, item.action);
      }
    });
    return Array.from(map.values());
  }, [auditItems]);

  const filteredAudit = React.useMemo(() => {
    if (auditActionFilter === "all") return auditItems;
    return auditItems.filter((item) => item.action === auditActionFilter);
  }, [auditActionFilter, auditItems]);

  const inWorkReports = React.useMemo(
    () => items.filter((item) => item.status === "open" || item.status === "in_review"),
    [items],
  );
  const closedReports = React.useMemo(
    () => items.filter((item) => item.status === "resolved" || item.status === "rejected"),
    [items],
  );

  const visibleReports = React.useMemo(() => {
    if (statusFilter === "all") return items;
    return items.filter((item) => item.status === statusFilter);
  }, [items, statusFilter]);

  function renderReportList(dataSource) {
    return (
      <List
        loading={loading}
        dataSource={dataSource}
        locale={{ emptyText: "Репорты не найдены" }}
        renderItem={(item) => (
          <List.Item
            actions={[
              <Button
                key="open"
                size="small"
                loading={Boolean(reportActionPending[`status:${item.id}:open`])}
                disabled={item.status === "open"}
                onClick={() => updateStatus(item.id, "open")}
              >
                Открыть
              </Button>,
              <Button
                key="review"
                size="small"
                loading={Boolean(reportActionPending[`status:${item.id}:in_review`])}
                disabled={item.status === "in_review"}
                onClick={() => updateStatus(item.id, "in_review")}
              >
                В работу
              </Button>,
              <Button
                key="resolve"
                size="small"
                type="primary"
                loading={Boolean(reportActionPending[`status:${item.id}:resolved`])}
                disabled={item.status === "resolved"}
                onClick={() => updateStatus(item.id, "resolved")}
              >
                Решен
              </Button>,
              <Button
                key="reject"
                size="small"
                danger
                loading={Boolean(reportActionPending[`status:${item.id}:rejected`])}
                disabled={item.status === "rejected"}
                onClick={() => updateStatus(item.id, "rejected")}
              >
                Отклонить
              </Button>,
              item.link_url ? (
                <Button key="open-target" size="small" type="link" onClick={() => window.open(item.link_url, "_blank")}>
                  Открыть объект
                </Button>
              ) : null,
              item.target_type === "course" || item.target_type === "comment" ? (
                <Popconfirm
                  key="hide"
                  title="Скрыть объект?"
                  okText="Скрыть"
                  cancelText="Отмена"
                  onConfirm={() => runTargetAction(item, "hide")}
                >
                  <Button size="small" loading={Boolean(reportActionPending[`target:${item.id}:hide`])}>
                    Скрыть объект
                  </Button>
                </Popconfirm>
              ) : null,
              item.target_type === "course" || item.target_type === "comment" ? (
                <Button
                  key="restore"
                  size="small"
                  loading={Boolean(reportActionPending[`target:${item.id}:restore`])}
                  onClick={() => runTargetAction(item, "restore")}
                >
                  Восстановить объект
                </Button>
              ) : null,
            ]}
          >
            <List.Item.Meta
              title={
                <Space wrap>
                  <Tag color="blue">{targetLabel(item.target_type)}</Tag>
                  <Tag color="cyan">{item.category}</Tag>
                  <Tag color="purple">{statusLabel(item.status)}</Tag>
                  {targetState[item.id]?.state === "hidden" ? <Tag color="volcano">Объект скрыт</Tag> : null}
                  {targetState[item.id]?.state === "restored" ? <Tag color="green">Объект восстановлен</Tag> : null}
                  <Typography.Text strong>{item.reason}</Typography.Text>
                </Space>
              }
              description={
                <Space direction="vertical" size={4}>
                  <Typography.Text type="secondary">Автор репорта: {getUserDisplayName(item.reporter)}</Typography.Text>
                  {item.details ? <Typography.Text>{item.details}</Typography.Text> : null}
                </Space>
              }
            />
          </List.Item>
        )}
      />
    );
  }

  if (!isAdmin) {
    return (
      <AppShell title="Модерация" subtitle="Доступ только для администратора">
        <Alert type="warning" showIcon message="Требуется роль администратора" />
      </AppShell>
    );
  }

  return (
    <AppShell title="Модерация" subtitle="Репорты и управление проблемным контентом">
      <Card className="panel-card">
        <Space direction="vertical" size={16} style={{ width: "100%" }}>
          <Segmented value={statusFilter} onChange={setStatusFilter} options={STATUS_OPTIONS} />

          {statusFilter === "all" ? (
            <Row gutter={[16, 16]}>
              <Col xs={24} lg={12}>
                <Card size="small" title={`В работе (${inWorkReports.length})`}>
                  {renderReportList(inWorkReports)}
                </Card>
              </Col>
              <Col xs={24} lg={12}>
                <Card size="small" title={`Закрытые (${closedReports.length})`}>
                  <Typography.Text type="secondary">
                    Закрытые тикеты автоматически удаляются через 14 дней после решения.
                  </Typography.Text>
                  <div style={{ marginTop: 10 }}>{renderReportList(closedReports)}</div>
                </Card>
              </Col>
            </Row>
          ) : (
            renderReportList(visibleReports)
          )}
        </Space>
      </Card>

      <Card className="panel-card" style={{ marginTop: 16 }}>
        <Space direction="vertical" size={12} style={{ width: "100%" }}>
          <Typography.Title level={5} style={{ margin: 0 }}>Управление пользователями</Typography.Title>
          <Space wrap>
            <Input
              placeholder="Причина блокировки"
              value={blockReason}
              onChange={(event) => setBlockReason(event.target.value)}
              style={{ width: 320 }}
            />
            <DatePicker
              showTime
              value={blockUntil}
              onChange={setBlockUntil}
              disabledDate={(current) => current && current < dayjs().startOf("day")}
              placeholder="Блокировать до..."
            />
          </Space>

          <List
            loading={usersLoading}
            dataSource={users}
            rowKey="id"
            locale={{ emptyText: "Пользователи не найдены" }}
            renderItem={(item) => (
              <List.Item
                actions={[
                  <Button key="to-student" size="small" onClick={() => changeRole(item.id, "student")}>Студент</Button>,
                  <Button key="to-teacher" size="small" onClick={() => changeRole(item.id, "teacher")}>Преподаватель</Button>,
                  <Button key="to-admin" size="small" type="primary" onClick={() => changeRole(item.id, "admin")}>Админ</Button>,
                  <Button key="block-temp" size="small" danger onClick={() => blockUser(item.id, false)}>Блок (врем.)</Button>,
                  <Button key="block-perm" size="small" danger onClick={() => blockUser(item.id, true)}>Блок (навсегда)</Button>,
                  <Button key="unblock" size="small" onClick={() => unblockUser(item.id)}>Разблокировать</Button>,
                ]}
              >
                <List.Item.Meta
                  title={
                    <Space wrap>
                      <Typography.Text strong>{getUserDisplayName(item)}</Typography.Text>
                      <Tag color={item.role === "admin" ? "red" : item.role === "teacher" ? "gold" : "cyan"}>{item.role}</Tag>
                      <Tag color={item.is_active ? "green" : "volcano"}>{item.is_active ? "активен" : "заблокирован"}</Tag>
                    </Space>
                  }
                  description={
                    <Space direction="vertical" size={2}>
                      <Typography.Text type="secondary">{item.email}</Typography.Text>
                      {item.blocked_until ? (
                        <Typography.Text type="secondary">Заблокирован до: {new Date(item.blocked_until).toLocaleString("ru-RU")}</Typography.Text>
                      ) : null}
                      {item.blocked_reason ? <Typography.Text type="secondary">Причина: {item.blocked_reason}</Typography.Text> : null}
                    </Space>
                  }
                />
              </List.Item>
            )}
          />
        </Space>
      </Card>

      <Card className="panel-card" style={{ marginTop: 16 }}>
        <Space direction="vertical" size={12} style={{ width: "100%" }}>
          <Space style={{ width: "100%", justifyContent: "space-between" }} wrap>
            <Typography.Title level={5} style={{ margin: 0 }}>
              Аудит-лог администратора
            </Typography.Title>
            <Space wrap>
              <Select
                value={auditActionFilter}
                onChange={setAuditActionFilter}
                style={{ minWidth: 220 }}
                options={[
                  { value: "all", label: "Все действия" },
                  ...auditActions.map((action) => ({ value: action, label: action })),
                ]}
              />
              <Button onClick={loadAudit}>Обновить</Button>
            </Space>
          </Space>

          <List
            loading={auditLoading}
            dataSource={filteredAudit}
            rowKey="id"
            locale={{ emptyText: "Записи аудит-лога отсутствуют" }}
            renderItem={(item) => (
              <List.Item>
                <List.Item.Meta
                  title={
                    <Space wrap>
                      <Tag color="geekblue">{item.action}</Tag>
                      <Tag>{item.target_type}</Tag>
                      <Typography.Text code>{item.target_id}</Typography.Text>
                    </Space>
                  }
                  description={
                    <Space direction="vertical" size={2}>
                      <Typography.Text type="secondary">
                        Администратор: {item.actor_name || item.actor_email || item.actor_user_id}
                      </Typography.Text>
                      <Typography.Text type="secondary">
                        Время: {new Date(item.created_at).toLocaleString("ru-RU")}
                      </Typography.Text>
                      {item.details_json ? (
                        <Typography.Text type="secondary">Детали: {JSON.stringify(item.details_json)}</Typography.Text>
                      ) : null}
                    </Space>
                  }
                />
              </List.Item>
            )}
          />
        </Space>
      </Card>
    </AppShell>
  );
}


