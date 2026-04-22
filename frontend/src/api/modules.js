import { api } from "./client";

export async function getModule(moduleId) {
  const { data } = await api.get(`/modules/${moduleId}`);
  return data;
}

export async function getModuleContents(moduleId) {
  const { data } = await api.get(`/modules/${moduleId}/contents`);
  return data;
}

export async function getModuleAssignments(moduleId) {
  const { data } = await api.get(`/modules/${moduleId}/assignments`);
  return data;
}

export async function createModuleAssignment(moduleId, payload) {
  const { data } = await api.post(`/modules/${moduleId}/assignments`, payload);
  return data;
}

export async function updateModuleAssignment(assignmentId, payload) {
  const { data } = await api.patch(`/assignments/${assignmentId}`, payload);
  return data;
}

export async function deleteModuleAssignment(assignmentId) {
  await api.delete(`/assignments/${assignmentId}`);
}

export async function uploadAssignmentAttachment(assignmentId, files) {
  const formData = new FormData();
  files.forEach((file) => {
    formData.append("files", file);
  });

  const { data } = await api.post(`/assignments/${assignmentId}/attachment`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function getMyAssignmentSubmissions(assignmentId) {
  const { data } = await api.get(`/assignments/${assignmentId}/submissions/me`);
  return data;
}

export async function getAssignmentSubmissions(assignmentId) {
  const { data } = await api.get(`/assignments/${assignmentId}/submissions`);
  return data;
}

export async function createAssignmentSubmission(assignmentId, answerMarkdown, files) {
  const formData = new FormData();
  if (answerMarkdown) {
    formData.append("answer_markdown", answerMarkdown);
  }
  (files || []).forEach((file) => formData.append("files", file));

  const { data } = await api.post(`/assignments/${assignmentId}/submissions`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function updateAssignmentSubmission(submissionId, answerMarkdown, files) {
  const formData = new FormData();
  if (answerMarkdown) {
    formData.append("answer_markdown", answerMarkdown);
  }
  (files || []).forEach((file) => formData.append("files", file));

  const { data } = await api.patch(`/assignment-submissions/${submissionId}`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function deleteAssignmentSubmission(submissionId) {
  await api.delete(`/assignment-submissions/${submissionId}`);
}

export async function gradeAssignmentSubmission(submissionId, payload) {
  const { data } = await api.patch(`/assignment-submissions/${submissionId}/grade`, payload);
  return data;
}

export async function createModuleTextContent(moduleId, payload) {
  const { data } = await api.post(`/modules/${moduleId}/contents/text`, payload);
  return data;
}

export async function createModuleLinkContent(moduleId, payload) {
  const { data } = await api.post(`/modules/${moduleId}/contents/link`, payload);
  return data;
}

export async function updateModuleContent(contentId, payload) {
  const { data } = await api.patch(`/module-contents/${contentId}`, payload);
  return data;
}

export async function replaceModuleContentFile(contentId, title, file) {
  const formData = new FormData();
  formData.append("title", title);
  formData.append("file", file);

  const { data } = await api.post(`/module-contents/${contentId}/replace-file`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function deleteModuleContent(contentId) {
  await api.delete(`/module-contents/${contentId}`);
}

export async function uploadModuleFileContent(moduleId, title, file, contentType) {
  const formData = new FormData();
  formData.append("title", title);
  formData.append("content_type", contentType);
  formData.append("file", file);

  const { data } = await api.post(`/modules/${moduleId}/contents/file`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function getModuleComments(moduleId) {
  const { data } = await api.get(`/modules/${moduleId}/comments`);
  return data;
}

export async function createModuleComment(moduleId, payload) {
  const { data } = await api.post(`/modules/${moduleId}/comments`, payload);
  return data;
}

export async function deleteModuleComment(commentId) {
  await api.delete(`/comments/${commentId}`);
}

export async function getModuleQuiz(moduleId) {
  const { data } = await api.get(`/modules/${moduleId}/quiz`);
  return data;
}

export async function createModuleQuiz(moduleId, payload) {
  const { data } = await api.post(`/modules/${moduleId}/quiz`, payload);
  return data;
}

export async function updateModuleQuiz(quizId, payload) {
  const { data } = await api.patch(`/quizzes/${quizId}`, payload);
  return data;
}

export async function deleteModuleQuiz(quizId) {
  await api.delete(`/quizzes/${quizId}`);
}

export async function submitQuiz(quizId, payload) {
  const { data } = await api.post(`/quizzes/${quizId}/submit`, payload);
  return data;
}

export async function getMyQuizAttempts(quizId) {
  const { data } = await api.get(`/quizzes/${quizId}/attempts/me`);
  return data;
}
