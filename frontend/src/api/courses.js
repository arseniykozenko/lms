import { api } from "./client";

export async function getCourses(params) {
  const { data } = await api.get("/courses", { params });
  return data;
}

export async function getCourseCategories() {
  const { data } = await api.get("/courses/categories/list");
  return data;
}

export async function getCourse(courseId) {
  const { data } = await api.get(`/courses/${courseId}`);
  return data;
}

export async function createCourse(payload) {
  const { data } = await api.post("/courses", payload);
  return data;
}

export async function updateCourse(courseId, payload) {
  const { data } = await api.patch(`/courses/${courseId}`, payload);
  return data;
}

export async function uploadCourseThumbnail(courseId, file) {
  const formData = new FormData();
  formData.append("file", file);

  const { data } = await api.post(`/courses/${courseId}/thumbnail`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function deleteCourse(courseId) {
  await api.delete(`/courses/${courseId}`);
}

export async function getCourseStudents(courseId) {
  const { data } = await api.get(`/courses/${courseId}/students`);
  return data;
}

export async function getCourseModules(courseId) {
  const { data } = await api.get(`/courses/${courseId}/modules`);
  return data;
}

export async function removeCourseStudent(courseId, studentId) {
  if (!courseId || !studentId || courseId === "undefined" || studentId === "undefined") {
    throw new Error("Invalid courseId/studentId for removeCourseStudent");
  }

  await api.delete(`/courses/${courseId}/students/${studentId}`);
}

export async function createModule(payload) {
  const { data } = await api.post("/modules", payload);
  return data;
}

export async function updateModule(moduleId, payload) {
  const { data } = await api.patch(`/modules/${moduleId}`, payload);
  return data;
}

export async function reorderCourseModules(courseId, modules) {
  const { data } = await api.post(`/modules/course/${courseId}/reorder`, {
    modules: modules.map((module) => ({ id: module.id })),
  });
  return data;
}

export async function enrollInCourse(courseId) {
  const { data } = await api.post(`/courses/${courseId}/enroll`);
  return data;
}

export async function downloadCourseStudentsCsv(courseId) {
  const response = await api.get(`/courses/${courseId}/students.csv`, { responseType: "blob" });
  return response.data;
}

export async function downloadCourseAnalyticsZip(courseId) {
  const response = await api.get(`/courses/${courseId}/analytics.zip`, { responseType: "blob" });
  return response.data;
}

export async function getCourseCollaborators(courseId) {
  const { data } = await api.get(`/courses/${courseId}/collaborators`);
  return data;
}

export async function getCourseAiInsights(courseId, studentsLimit = 15) {
  const { data } = await api.get(`/courses/${courseId}/ai-insights`, {
    params: { students_limit: studentsLimit },
  });
  return data;
}

export async function getStudentCourseAiInsights(courseId) {
  const { data } = await api.get(`/courses/${courseId}/ai-insights/student`);
  return data;
}

export async function inviteCourseCollaborator(courseId, payload) {
  const { data } = await api.post(`/courses/${courseId}/collaborators/invite`, payload);
  return data;
}

export async function removeCourseCollaborator(courseId, collaboratorUserId) {
  await api.delete(`/courses/${courseId}/collaborators/${collaboratorUserId}`);
}

export async function getMyCollaborationInvites() {
  const { data } = await api.get("/courses/collaboration-invites/me");
  return data;
}

export async function acceptCollaborationInvite(inviteId) {
  const { data } = await api.post(`/courses/collaboration-invites/${inviteId}/accept`);
  return data;
}

export async function declineCollaborationInvite(inviteId) {
  const { data } = await api.post(`/courses/collaboration-invites/${inviteId}/decline`);
  return data;
}

export async function searchTeachers(query) {
  const { data } = await api.get("/users/teachers/search", { params: { q: query, limit: 10 } });
  return data;
}



