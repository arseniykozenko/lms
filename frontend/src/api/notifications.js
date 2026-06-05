import { api } from "./client";

export async function getMyNotifications() {
  const { data } = await api.get("/users/me/notifications");
  return data;
}

export async function markNotificationRead(notificationId) {
  const { data } = await api.post(`/users/me/notifications/${notificationId}/read`);
  return data;
}

export async function markAllNotificationsRead() {
  await api.post("/users/me/notifications/read-all");
}

export async function deleteNotification(notificationId) {
  await api.delete(`/users/me/notifications/${notificationId}`);
}

export async function deleteReadNotifications() {
  await api.delete("/users/me/notifications/read");
}
