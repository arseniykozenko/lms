import { api } from "./client";

export async function listAdminUsers() {
  const { data } = await api.get("/users/admin/users");
  return data;
}

export async function setUserRoleByAdmin(userId, role) {
  const { data } = await api.post(`/users/admin/users/${userId}/role`, { role });
  return data;
}

export async function blockUserByAdmin(userId, payload) {
  const { data } = await api.post(`/users/admin/users/${userId}/block`, payload);
  return data;
}

export async function unblockUserByAdmin(userId) {
  const { data } = await api.post(`/users/admin/users/${userId}/unblock`);
  return data;
}

export async function listAdminAuditLogs(limit = 100) {
  const { data } = await api.get("/users/admin/audit-logs", { params: { limit } });
  return data;
}
