import { api } from "./client";

const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api/v1";

export async function getChatConversations() {
  const { data } = await api.get("/chat/conversations");
  return data;
}

export async function getChatMessages(partnerId) {
  const { data } = await api.get(`/chat/messages/${partnerId}`);
  return data;
}

export async function sendChatMessage(payload) {
  const { data } = await api.post("/chat/messages", payload);
  return data;
}

export async function markChatConversationRead(partnerId) {
  await api.post(`/chat/messages/${partnerId}/read`);
}

export async function getChatGroups() {
  const { data } = await api.get("/chat/groups");
  return data;
}

export async function createChatGroup(payload) {
  const { data } = await api.post("/chat/groups", payload);
  return data;
}

export async function getChatGroupMessages(groupId) {
  const { data } = await api.get(`/chat/groups/${groupId}/messages`);
  return data;
}

export async function sendChatGroupMessage(groupId, payload) {
  const { data } = await api.post(`/chat/groups/${groupId}/messages`, payload);
  return data;
}

export function createChatWebSocket(token) {
  const baseUrl = API_URL.replace(/^http/i, "ws");
  return new WebSocket(`${baseUrl}/chat/ws?token=${encodeURIComponent(token)}`);
}
