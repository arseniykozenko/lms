import { combine, createEffect, createEvent, createStore, sample } from "effector";

import {
  createAssignmentSubmission,
  deleteAssignmentSubmission,
  createModuleComment,
  createModuleAssignment,
  createModuleLinkContent,
  createModuleQuiz,
  createModuleTextContent,
  deleteModuleComment,
  deleteModuleAssignment,
  deleteModuleContent,
  deleteModuleQuiz,
  getAssignmentSubmissions,
  getModule,
  getModuleAssignments,
  getModuleComments,
  getModuleContents,
  getModuleQuiz,
  getMyAssignmentSubmissions,
  getMyQuizAttempts,
  gradeAssignmentSubmission,
  replaceModuleContentFile,
  submitQuiz,
  updateAssignmentSubmission,
  updateModuleAssignment,
  updateModuleContent,
  updateModuleQuiz,
  uploadAssignmentAttachment,
  uploadModuleFileContent,
} from "../api/modules";

export const modulePageOpened = createEvent();
export const modulePageReset = createEvent();
export const quizAttemptRestarted = createEvent();

export const loadModuleFx = createEffect(async (moduleId) => getModule(moduleId));
export const loadModuleContentsFx = createEffect(async (moduleId) => getModuleContents(moduleId));
export const loadModuleAssignmentsFx = createEffect(async (moduleId) => getModuleAssignments(moduleId));
export const loadModuleCommentsFx = createEffect(async (moduleId) => getModuleComments(moduleId));
export const loadModuleQuizFx = createEffect(async (moduleId) => {
  try {
    return await getModuleQuiz(moduleId);
  } catch (error) {
    if (error?.response?.status === 404) {
      return null;
    }
    throw error;
  }
});
export const loadMyQuizAttemptsFx = createEffect(async (quizId) => {
  if (!quizId) return [];
  return getMyQuizAttempts(quizId);
});

export const createModuleTextContentFx = createEffect(async ({ moduleId, payload }) => createModuleTextContent(moduleId, payload));
export const createModuleLinkContentFx = createEffect(async ({ moduleId, payload }) => createModuleLinkContent(moduleId, payload));
export const uploadModuleFileContentFx = createEffect(async ({ moduleId, title, file, contentType }) =>
  uploadModuleFileContent(moduleId, title, file, contentType),
);
export const createModuleAssignmentFx = createEffect(async ({ moduleId, payload }) => createModuleAssignment(moduleId, payload));
export const updateModuleAssignmentFx = createEffect(async ({ assignmentId, payload }) => updateModuleAssignment(assignmentId, payload));
export const deleteModuleAssignmentFx = createEffect(async ({ assignmentId, moduleId }) => {
  await deleteModuleAssignment(assignmentId);
  return moduleId;
});
export const uploadAssignmentAttachmentFx = createEffect(async ({ assignmentId, files }) =>
  uploadAssignmentAttachment(assignmentId, files),
);
export const loadAssignmentSubmissionsFx = createEffect(async ({ assignmentId, canManage }) => {
  const submissions = canManage ? await getAssignmentSubmissions(assignmentId) : await getMyAssignmentSubmissions(assignmentId);
  return { assignmentId, submissions };
});
export const createAssignmentSubmissionFx = createEffect(async ({ assignmentId, answerMarkdown, files }) =>
  createAssignmentSubmission(assignmentId, answerMarkdown, files),
);
export const updateAssignmentSubmissionFx = createEffect(async ({ submissionId, answerMarkdown, files }) =>
  updateAssignmentSubmission(submissionId, answerMarkdown, files),
);
export const deleteAssignmentSubmissionFx = createEffect(async ({ submissionId, assignmentId }) => {
  await deleteAssignmentSubmission(submissionId);
  return { submissionId, assignmentId };
});
export const gradeAssignmentSubmissionFx = createEffect(async ({ submissionId, payload }) =>
  gradeAssignmentSubmission(submissionId, payload),
);
export const updateModuleContentFx = createEffect(async ({ contentId, payload }) => updateModuleContent(contentId, payload));
export const replaceModuleContentFileFx = createEffect(async ({ contentId, title, file }) =>
  replaceModuleContentFile(contentId, title, file),
);
export const deleteModuleContentFx = createEffect(async ({ contentId, moduleId }) => {
  await deleteModuleContent(contentId);
  return moduleId;
});

export const createModuleCommentFx = createEffect(async ({ moduleId, payload }) => createModuleComment(moduleId, payload));
export const deleteModuleCommentFx = createEffect(async ({ commentId, moduleId }) => {
  await deleteModuleComment(commentId);
  return moduleId;
});

export const createModuleQuizFx = createEffect(async ({ moduleId, payload }) => createModuleQuiz(moduleId, payload));
export const updateModuleQuizFx = createEffect(async ({ quizId, payload }) => updateModuleQuiz(quizId, payload));
export const deleteModuleQuizFx = createEffect(async ({ quizId, moduleId }) => {
  await deleteModuleQuiz(quizId);
  return moduleId;
});
export const submitQuizFx = createEffect(async ({ quizId, payload }) => submitQuiz(quizId, payload));

export const $selectedModule = createStore(null)
  .on(loadModuleFx.doneData, (_, module) => module)
  .reset(modulePageReset);

export const $moduleContents = createStore([])
  .on(loadModuleContentsFx.doneData, (_, contents) => contents)
  .reset(modulePageReset);

export const $moduleAssignments = createStore([])
  .on(loadModuleAssignmentsFx.doneData, (_, assignments) => assignments)
  .on(createModuleAssignmentFx.doneData, (assignments, assignment) => [assignment, ...assignments])
  .on(updateModuleAssignmentFx.doneData, (assignments, assignment) =>
    assignments.map((item) => (item.id === assignment.id ? assignment : item)),
  )
  .on(uploadAssignmentAttachmentFx.doneData, (assignments, assignment) =>
    assignments.map((item) => (item.id === assignment.id ? assignment : item)),
  )
  .reset(modulePageReset);

export const $assignmentSubmissionsByAssignment = createStore({})
  .on(loadAssignmentSubmissionsFx.doneData, (state, { assignmentId, submissions }) => ({
    ...state,
    [assignmentId]: submissions,
  }))
  .reset(modulePageReset);

export const $moduleComments = createStore([])
  .on(loadModuleCommentsFx.doneData, (_, comments) => comments)
  .reset(modulePageReset);

export const $moduleQuiz = createStore(null)
  .on(loadModuleQuizFx.doneData, (_, quiz) => quiz)
  .on(createModuleQuizFx.doneData, (_, quiz) => quiz)
  .on(updateModuleQuizFx.doneData, (_, quiz) => quiz)
  .on(deleteModuleQuizFx.done, () => null)
  .reset(modulePageReset);

export const $myQuizAttempts = createStore([])
  .on(loadMyQuizAttemptsFx.doneData, (_, attempts) => attempts)
  .on(createModuleQuizFx.done, () => [])
  .on(deleteModuleQuizFx.done, () => [])
  .reset(modulePageReset);

export const $quizSubmitResult = createStore(null)
  .on(submitQuizFx.doneData, (_, result) => result)
  .on(loadMyQuizAttemptsFx.doneData, (_, attempts) => attempts[0] ?? null)
  .reset(modulePageReset, createModuleQuizFx.done, quizAttemptRestarted, deleteModuleQuizFx.done);

export const $selectedModulePending = loadModuleFx.pending;
export const $moduleContentsPending = loadModuleContentsFx.pending;
export const $moduleAssignmentsPending = loadModuleAssignmentsFx.pending;
export const $moduleCommentsPending = loadModuleCommentsFx.pending;
export const $moduleQuizPending = loadModuleQuizFx.pending;
export const $moduleContentCreatePending = createModuleTextContentFx.pending;
export const $moduleLinkCreatePending = createModuleLinkContentFx.pending;
export const $moduleFileCreatePending = uploadModuleFileContentFx.pending;
export const $moduleAssignmentCreatePending = createModuleAssignmentFx.pending;
export const $moduleAssignmentUpdatePending = updateModuleAssignmentFx.pending;
export const $moduleAssignmentDeletePending = deleteModuleAssignmentFx.pending;
export const $moduleAssignmentAttachmentPending = uploadAssignmentAttachmentFx.pending;
export const $assignmentSubmissionsPending = loadAssignmentSubmissionsFx.pending;
export const $assignmentSubmissionCreatePending = createAssignmentSubmissionFx.pending;
export const $assignmentSubmissionUpdatePending = updateAssignmentSubmissionFx.pending;
export const $assignmentSubmissionDeletePending = deleteAssignmentSubmissionFx.pending;
export const $assignmentSubmissionGradePending = gradeAssignmentSubmissionFx.pending;
export const $moduleContentUpdatePending = updateModuleContentFx.pending;
export const $moduleContentReplacePending = replaceModuleContentFileFx.pending;
export const $moduleContentDeletePending = deleteModuleContentFx.pending;
export const $moduleCommentCreatePending = createModuleCommentFx.pending;
export const $moduleCommentDeletePending = deleteModuleCommentFx.pending;
export const $moduleQuizCreatePending = createModuleQuizFx.pending;
export const $moduleQuizUpdatePending = updateModuleQuizFx.pending;
export const $moduleQuizDeletePending = deleteModuleQuizFx.pending;
export const $quizSubmitPending = submitQuizFx.pending;

export const $moduleInteractionsPending = combine(
  createModuleCommentFx.pending,
  deleteModuleCommentFx.pending,
  createModuleQuizFx.pending,
  updateModuleQuizFx.pending,
  deleteModuleQuizFx.pending,
  updateModuleContentFx.pending,
    replaceModuleContentFileFx.pending,
    deleteModuleContentFx.pending,
    createModuleAssignmentFx.pending,
    updateModuleAssignmentFx.pending,
    deleteModuleAssignmentFx.pending,
    uploadAssignmentAttachmentFx.pending,
    createAssignmentSubmissionFx.pending,
    updateAssignmentSubmissionFx.pending,
    deleteAssignmentSubmissionFx.pending,
    gradeAssignmentSubmissionFx.pending,
    submitQuizFx.pending,
    (
    commentCreatePending,
    commentDeletePending,
    quizCreatePending,
      quizUpdatePending,
      quizDeletePending,
      contentUpdatePending,
      contentReplacePending,
      contentDeletePending,
      assignmentCreatePending,
      assignmentUpdatePending,
      assignmentDeletePending,
      assignmentAttachmentPending,
      assignmentSubmissionPending,
      assignmentSubmissionUpdatePending,
      assignmentSubmissionDeletePending,
      assignmentGradePending,
      submitPending,
    ) =>
    commentCreatePending ||
    commentDeletePending ||
    quizCreatePending ||
    quizUpdatePending ||
    quizDeletePending ||
    contentUpdatePending ||
    contentReplacePending ||
    contentDeletePending ||
    assignmentCreatePending ||
    assignmentUpdatePending ||
    assignmentDeletePending ||
    assignmentAttachmentPending ||
    assignmentSubmissionPending ||
    assignmentSubmissionUpdatePending ||
    assignmentSubmissionDeletePending ||
    assignmentGradePending ||
    submitPending,
);

sample({
  clock: modulePageOpened,
  target: [loadModuleFx, loadModuleContentsFx, loadModuleAssignmentsFx, loadModuleCommentsFx, loadModuleQuizFx],
});

sample({
  clock: [
    createModuleTextContentFx.done,
    createModuleLinkContentFx.done,
    uploadModuleFileContentFx.done,
    updateModuleContentFx.done,
    replaceModuleContentFileFx.done,
  ],
  fn: ({ result }) => result.module_id,
  target: loadModuleContentsFx,
});

sample({
  clock: [createModuleAssignmentFx.done, updateModuleAssignmentFx.done, uploadAssignmentAttachmentFx.done],
  fn: ({ result }) => result.module_id,
  target: loadModuleAssignmentsFx,
});

sample({
  clock: deleteModuleAssignmentFx.doneData,
  target: loadModuleAssignmentsFx,
});

sample({
  clock: deleteModuleContentFx.doneData,
  target: loadModuleContentsFx,
});

sample({
  clock: createModuleCommentFx.done,
  fn: ({ result }) => result.module_id,
  target: loadModuleCommentsFx,
});

sample({
  clock: deleteModuleCommentFx.doneData,
  target: loadModuleCommentsFx,
});

sample({
  clock: createModuleQuizFx.doneData,
  fn: (quiz) => quiz.id,
  target: loadMyQuizAttemptsFx,
});

sample({
  clock: updateModuleQuizFx.doneData,
  fn: (quiz) => quiz.id,
  target: loadMyQuizAttemptsFx,
});

sample({
  clock: loadModuleQuizFx.doneData,
  filter: (quiz) => Boolean(quiz?.id),
  fn: (quiz) => quiz.id,
  target: loadMyQuizAttemptsFx,
});

sample({
  clock: submitQuizFx.doneData,
  fn: (result) => result.quiz_id,
  target: loadMyQuizAttemptsFx,
});

sample({
  clock: deleteModuleQuizFx.doneData,
  target: loadModuleQuizFx,
});

sample({
  clock: createAssignmentSubmissionFx.doneData,
  fn: (submission) => ({ assignmentId: submission.assignment_id, canManage: false }),
  target: loadAssignmentSubmissionsFx,
});

sample({
  clock: updateAssignmentSubmissionFx.doneData,
  fn: (submission) => ({ assignmentId: submission.assignment_id, canManage: false }),
  target: loadAssignmentSubmissionsFx,
});

sample({
  clock: deleteAssignmentSubmissionFx.doneData,
  fn: ({ assignmentId }) => ({ assignmentId, canManage: false }),
  target: loadAssignmentSubmissionsFx,
});

sample({
  clock: gradeAssignmentSubmissionFx.doneData,
  fn: (submission) => ({ assignmentId: submission.assignment_id, canManage: true }),
  target: loadAssignmentSubmissionsFx,
});
