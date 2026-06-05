import React from "react";
import { MessageOutlined, PlusOutlined, SendOutlined, TeamOutlined, UserOutlined } from "@ant-design/icons";
import {
  Avatar,
  Badge,
  Button,
  Card,
  Empty,
  Input,
  List,
  Modal,
  Segmented,
  Select,
  Space,
  Spin,
  Tag,
  Typography,
  message,
} from "antd";
import { useUnit } from "effector-react";
import { useLocation } from "react-router-dom";

import {
  createChatGroup,
  createChatWebSocket,
  getChatConversations,
  getChatGroupMessages,
  getChatGroups,
  getChatMessages,
  markChatConversationRead,
  sendChatGroupMessage,
  sendChatMessage,
} from "../api/chat";
import { AppShell } from "../components/AppShell";
import { getErrorMessage } from "../lib/errors";
import { $user } from "../models/auth";

const STORAGE_KEY = "lms-auth";

function readStoredToken() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw)?.token || null : null;
  } catch {
    return null;
  }
}

function upsertMessage(messages, nextMessage) {
  const hasMessage = messages.some((item) => item.id === nextMessage.id);
  if (hasMessage) return messages.map((item) => (item.id === nextMessage.id ? nextMessage : item));
  return [...messages, nextMessage].sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
}

export function ChatPage() {
  const location = useLocation();
  const partnerIdFromQuery = React.useMemo(() => new URLSearchParams(location.search).get("partner"), [location.search]);
  const user = useUnit($user);
  const [messageApi, contextHolder] = message.useMessage();

  const [mode, setMode] = React.useState("direct");
  const [conversations, setConversations] = React.useState([]);
  const [groups, setGroups] = React.useState([]);
  const [selectedPartnerId, setSelectedPartnerId] = React.useState(location.state?.partnerId || partnerIdFromQuery || null);
  const [selectedGroupId, setSelectedGroupId] = React.useState(null);
  const [messages, setMessages] = React.useState([]);
  const [draft, setDraft] = React.useState("");
  const [loading, setLoading] = React.useState(true);
  const [sending, setSending] = React.useState(false);

  const [createOpen, setCreateOpen] = React.useState(false);
  const [groupTitle, setGroupTitle] = React.useState("");
  const [groupMembers, setGroupMembers] = React.useState([]);

  const selectedConversation = conversations.find((item) => item.partner_id === selectedPartnerId) || null;
  const selectedGroup = groups.find((item) => item.id === selectedGroupId) || null;

  const loadBase = React.useCallback(async () => {
    setLoading(true);
    try {
      const [nextConversations, nextGroups] = await Promise.all([getChatConversations(), getChatGroups()]);
      setConversations(nextConversations);
      setGroups(nextGroups);
      if (!selectedPartnerId && nextConversations[0]) setSelectedPartnerId(nextConversations[0].partner_id);
      if (!selectedGroupId && nextGroups[0]) setSelectedGroupId(nextGroups[0].id);
    } catch (error) {
      messageApi.error(getErrorMessage(error, "Не удалось загрузить чат"));
    } finally {
      setLoading(false);
    }
  }, [messageApi, selectedGroupId, selectedPartnerId]);

  const loadMessages = React.useCallback(async () => {
    try {
      if (mode === "direct" && selectedPartnerId) {
        const items = await getChatMessages(selectedPartnerId);
        setMessages(items);
        await markChatConversationRead(selectedPartnerId);
      } else if (mode === "group" && selectedGroupId) {
        const items = await getChatGroupMessages(selectedGroupId);
        setMessages(items);
      } else {
        setMessages([]);
      }
    } catch (error) {
      messageApi.error(getErrorMessage(error, "Не удалось загрузить сообщения"));
    }
  }, [messageApi, mode, selectedGroupId, selectedPartnerId]);

  React.useEffect(() => {
    loadBase();
  }, [loadBase]);

  React.useEffect(() => {
    loadMessages();
  }, [loadMessages]);

  React.useEffect(() => {
    const token = readStoredToken();
    if (!token) return undefined;
    const socket = createChatWebSocket(token);

    socket.onmessage = async (event) => {
      const payload = JSON.parse(event.data);
      if (payload.type === "chat.message") {
        const msg = payload.message;
        const partnerId = msg.sender_id === user?.id ? msg.recipient_id : msg.sender_id;
        if (mode === "direct" && selectedPartnerId === partnerId) {
          setMessages((current) => upsertMessage(current, msg));
        }
      }
      if (payload.type === "chat.group_message") {
        const msg = payload.message;
        if (mode === "group" && selectedGroupId === msg.group_id) {
          setMessages((current) => upsertMessage(current, msg));
        }
      }
    };

    return () => socket.close();
  }, [mode, selectedGroupId, selectedPartnerId, user?.id]);

  async function handleSend() {
    const content = draft.trim();
    if (!content) return;

    setSending(true);
    try {
      if (mode === "direct" && selectedPartnerId) {
        const created = await sendChatMessage({ recipient_id: selectedPartnerId, content });
        setMessages((current) => upsertMessage(current, created));
      }
      if (mode === "group" && selectedGroupId) {
        const created = await sendChatGroupMessage(selectedGroupId, { content });
        setMessages((current) => upsertMessage(current, created));
      }
      setDraft("");
    } catch (error) {
      messageApi.error(getErrorMessage(error, "Не удалось отправить сообщение"));
    } finally {
      setSending(false);
    }
  }

  async function handleCreateGroup() {
    try {
      const created = await createChatGroup({ title: groupTitle, member_ids: groupMembers });
      setGroups((current) => [created, ...current]);
      setSelectedGroupId(created.id);
      setMode("group");
      setCreateOpen(false);
      setGroupTitle("");
      setGroupMembers([]);
    } catch (error) {
      messageApi.error(getErrorMessage(error, "Не удалось создать группу"));
    }
  }

  const memberCandidates = conversations
    .filter((item) => item.partner_role === "student")
    .map((item) => ({ label: `${item.partner_name} (${item.partner_email})`, value: item.partner_id }));

  const listData = mode === "direct" ? conversations : groups;
  const activeTitle = mode === "direct" ? selectedConversation?.partner_name : selectedGroup?.title;

  return (
    <AppShell title="Чаты" subtitle="Личные и групповые чаты курса">
      {contextHolder}
      <div style={{ display: "grid", gridTemplateColumns: "340px minmax(0, 1fr)", gap: 20, minHeight: 640 }}>
        <Card
          title={<Segmented value={mode} onChange={setMode} options={[{ label: "Личные", value: "direct" }, { label: "Группы", value: "group" }]} />}
          extra={
            mode === "group" && (user?.role === "teacher" || user?.role === "admin") ? (
              <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>
                Группа
              </Button>
            ) : null
          }
          styles={{ body: { padding: 0 } }}
        >
          {loading ? (
            <div style={{ padding: 24, textAlign: "center" }}>
              <Spin />
            </div>
          ) : listData.length ? (
            <List
              dataSource={listData}
              renderItem={(item) => {
                const active = mode === "direct" ? item.partner_id === selectedPartnerId : item.id === selectedGroupId;
                return (
                  <List.Item
                    style={{ cursor: "pointer", paddingInline: 16, background: active ? "rgba(24,144,255,.08)" : "transparent" }}
                    onClick={() => (mode === "direct" ? setSelectedPartnerId(item.partner_id) : setSelectedGroupId(item.id))}
                  >
                    <List.Item.Meta
                      avatar={
                        <Badge count={item.unread_count || 0}>
                          {mode === "direct" ? (
                            <Avatar src={item.partner_profile_photo_url || undefined} icon={<UserOutlined />} />
                          ) : (
                            <Avatar icon={<TeamOutlined />} />
                          )}
                        </Badge>
                      }
                      title={<Typography.Text strong>{mode === "direct" ? item.partner_name : item.title}</Typography.Text>}
                      description={mode === "direct" ? item.partner_email : `${item.members?.length || 0} участников`}
                    />
                  </List.Item>
                );
              }}
            />
          ) : (
            <div style={{ padding: 24 }}>
              <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="Список пока пуст" />
            </div>
          )}
        </Card>

        <Card
          title={activeTitle || "Переписка"}
          styles={{ body: { display: "flex", flexDirection: "column", gap: 16, minHeight: 560 } }}
        >
          {!activeTitle ? (
            <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="Выберите чат слева" style={{ margin: "auto 0" }} />
          ) : (
            <>
              <div style={{ flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", gap: 12 }}>
                {messages.length ? (
                  messages.map((item) => {
                    const own = item.sender_id === user?.id;
                    return (
                      <div key={item.id} style={{ alignSelf: own ? "flex-end" : "flex-start", maxWidth: "82%", display: "flex", gap: 8, flexDirection: own ? "row-reverse" : "row", alignItems: "flex-end" }}>
                        <Avatar
                          size={28}
                          src={item.sender_profile_photo_url || undefined}
                          icon={<UserOutlined />}
                        />
                        <div className={`chat-message-bubble ${own ? "chat-message-bubble-own" : "chat-message-bubble-peer"}`} style={{ maxWidth: "100%" }}>
                          <Typography.Text strong style={{ color: "inherit" }}>{item.sender_name}</Typography.Text>
                          <Typography.Paragraph style={{ color: "inherit", marginBottom: 8 }}>{item.content}</Typography.Paragraph>
                          <Typography.Text style={{ fontSize: 12, opacity: 0.8 }}>{new Date(item.created_at).toLocaleString("ru-RU")}</Typography.Text>
                        </div>
                      </div>
                    );
                  })
                ) : (
                  <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="Сообщений пока нет" style={{ margin: "auto 0" }} />
                )}
              </div>
              <Space.Compact style={{ width: "100%" }}>
                <Input.TextArea
                  autoSize={{ minRows: 2, maxRows: 5 }}
                  value={draft}
                  onChange={(event) => setDraft(event.target.value)}
                  onPressEnter={(event) => {
                    if (!event.shiftKey) {
                      event.preventDefault();
                      handleSend();
                    }
                  }}
                  placeholder="Введите сообщение"
                />
                <Button type="primary" icon={<SendOutlined />} loading={sending} onClick={handleSend}>
                  Отправить
                </Button>
              </Space.Compact>
            </>
          )}
        </Card>
      </div>

      <Modal
        title="Новая группа"
        open={createOpen}
        onCancel={() => setCreateOpen(false)}
        onOk={handleCreateGroup}
        okText="Создать"
      >
        <Space direction="vertical" size={12} style={{ width: "100%" }}>
          <Input placeholder="Название группы" value={groupTitle} onChange={(e) => setGroupTitle(e.target.value)} />
          <Select
            mode="multiple"
            placeholder="Выберите студентов"
            value={groupMembers}
            onChange={setGroupMembers}
            options={memberCandidates}
            style={{ width: "100%" }}
          />
          <Tag>В группу можно добавить студентов, с которыми у вас уже есть чат по курсу.</Tag>
        </Space>
      </Modal>
    </AppShell>
  );
}

