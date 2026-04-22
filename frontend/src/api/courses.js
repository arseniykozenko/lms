import { api } from "./client";

export async function getCourses() {
  const { data } = await api.get("/courses");
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

