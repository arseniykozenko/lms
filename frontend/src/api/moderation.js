import { api } from "./client";

export async function createReport(payload) {
  const { data } = await api.post("/moderation/reports", payload);
  return data;
}

export async function listReports(status) {
  const { data } = await api.get("/moderation/admin/reports", {
    params: status ? { status } : undefined,
  });
  return data;
}

export async function reviewReport(reportId, payload) {
  const { data } = await api.patch(`/moderation/admin/reports/${reportId}`, payload);
  return data;
}

export async function hideCourseByAdmin(courseId) {
  await api.post(`/moderation/admin/courses/${courseId}/hide`);
}

export async function restoreCourseByAdmin(courseId) {
  await api.post(`/moderation/admin/courses/${courseId}/restore`);
}

export async function hideCommentByAdmin(commentId) {
  await api.post(`/moderation/admin/comments/${commentId}/hide`);
}

export async function restoreCommentByAdmin(commentId) {
  await api.post(`/moderation/admin/comments/${commentId}/restore`);
}
