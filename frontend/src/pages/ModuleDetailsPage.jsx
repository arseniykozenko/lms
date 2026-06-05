import React from "react";
import { Col, Form, Input, Modal, Row, Select, message } from "antd";
import { useUnit } from "effector-react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";

import { AppShell } from "../components/AppShell";
import { ModuleManagementDrawers } from "../components/modules/ModuleManagementDrawers";
import { ModuleLoadingState, ModuleNotFoundState } from "../components/modules/ModulePageState";
import { StudentModuleWorkspace } from "../components/modules/StudentModuleWorkspace";
import { TeacherModuleOverviewCard } from "../components/modules/TeacherModuleOverviewCard";
import { TeacherModuleWorkspace } from "../components/modules/TeacherModuleWorkspace";
import { fromDateTimeLocalValue, toDateTimeLocalValue } from "../components/modules/moduleHelpers";
import { PageBreadcrumbs } from "../components/shared/PageBreadcrumbs";
import { getErrorMessage } from "../lib/errors";
import { createReport } from "../api/moderation";
import { $courses, $user } from "../models/auth";
import { $selectedCourseModules, loadCourseModulesFx } from "../models/courses";
import {
  $assignmentSubmissionCreatePending,
  $assignmentSubmissionDeletePending,
  $assignmentSubmissionGradePending,
  $assignmentSubmissionUpdatePending,
  $assignmentSubmissionsByAssignment,
  $moduleAssignmentAttachmentPending,
  $moduleAssignmentAttachmentClearPending,
  $moduleAssignmentCreatePending,
  $moduleAssignmentDeletePending,
  $moduleAssignmentUpdatePending,
  $moduleAssignments,
  $moduleAssignmentsPending,
  $moduleCommentCreatePending,
  $moduleCommentDeletePending,
  $moduleComments,
  $moduleCommentsPending,
  $moduleContentCreatePending,
  $moduleContentDeletePending,
  $moduleContentReplacePending,
  $moduleContentUpdatePending,
  $moduleContents,
  $moduleContentsPending,
  $moduleFileCreatePending,
  $moduleLinkCreatePending,
  $moduleQuiz,
  $moduleQuizCreatePending,
  $moduleQuizDeletePending,
  $moduleQuizPending,
  $moduleQuizUpdatePending,
  $myQuizAttempts,
  $quizSubmitPending,
  $quizSubmitResult,
  $selectedModule,
  $selectedModulePending,
  createAssignmentSubmissionFx,
  createModuleAssignmentFx,
  createModuleCommentFx,
  createModuleLinkContentFx,
  createModuleQuizFx,
  createModuleTextContentFx,
  deleteAssignmentSubmissionFx,
  deleteModuleAssignmentFx,
  deleteModuleCommentFx,
  deleteModuleContentFx,
  deleteModuleQuizFx,
  gradeAssignmentSubmissionFx,
  loadAssignmentSubmissionsFx,
  loadModuleAssignmentsFx,
  loadModuleAssignmentsQuietFx,
  loadModuleCommentsFx,
  loadModuleCommentsQuietFx,
  loadModuleContentsFx,
  loadModuleFx,
  loadModuleQuizFx,
  loadMyQuizAttemptsFx,
  modulePageOpened,
  modulePageReset,
  quizAttemptRestarted,
  replaceModuleContentFileFx,
  submitQuizFx,
  updateAssignmentSubmissionFx,
  updateModuleAssignmentFx,
  updateModuleContentFx,
  updateModuleQuizFx,
  uploadAssignmentAttachmentFx,
  clearAssignmentAttachmentFx,
  uploadModuleFileContentFx,
} from "../models/modules";

const defaultContentValues = {
  content_type: "text",
  title: "",
  text_content: "",
  source_url: "",
};

const defaultQuizValues = {
  title: "",
  due_at: "",
  is_published: true,
  questions: [{ content: "", options: ["", ""], correct_option: "", explanation: "" }],
};

const defaultAssignmentValues = {
  title: "",
  instructions_markdown: "",
  max_score: 100,
  due_at: "",
  is_published: true,
};

const STUDENT_MODULE_REFRESH_MS = 90000;

export function ModuleDetailsPage() {
  const { moduleId } = useParams();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [
    user,
    myCourses,
    courseModules,
    module,
    contents,
    assignments,
    assignmentSubmissionsByAssignment,
    comments,
    quiz,
    attempts,
    quizSubmitResult,
    modulePending,
    contentsPending,
    assignmentsPending,
    commentsPending,
    quizPending,
    creatingText,
    creatingLink,
    uploadingFile,
    creatingAssignment,
    updatingAssignment,
    deletingAssignment,
    uploadingAssignmentAttachment,
    clearingAssignmentAttachment,
    creatingAssignmentSubmission,
    updatingAssignmentSubmission,
    deletingAssignmentSubmission,
    gradingAssignmentSubmission,
    updatingContent,
    replacingContentFile,
    deletingContent,
    creatingComment,
    deletingComment,
    creatingQuiz,
    updatingQuiz,
    deletingQuiz,
    submittingQuiz,
    openModulePage,
    resetModulePage,
    submitTextContent,
    submitLinkContent,
    submitFileContent,
    submitCreateAssignment,
    submitUpdateAssignment,
    submitDeleteAssignment,
    submitUploadAssignmentAttachment,
    submitClearAssignmentAttachment,
    loadAssignmentSubmissions,
    refreshModule,
    refreshModuleAssignments,
    refreshModuleAssignmentsQuiet,
    refreshModuleComments,
    refreshModuleCommentsQuiet,
    refreshModuleContents,
    refreshModuleQuiz,
    refreshMyQuizAttempts,
    submitAssignmentSubmission,
    submitAssignmentSubmissionUpdate,
    submitAssignmentSubmissionDelete,
    submitGradeAssignmentSubmission,
    submitContentUpdate,
    submitContentFileReplace,
    submitContentDelete,
    submitComment,
    submitCommentDelete,
    submitCreateQuiz,
    submitQuizUpdate,
    submitQuizDelete,
    submitQuizAttempt,
    loadCourseModules,
    restartQuizAttempt,
  ] = useUnit([
    $user,
    $courses,
    $selectedCourseModules,
    $selectedModule,
    $moduleContents,
    $moduleAssignments,
    $assignmentSubmissionsByAssignment,
    $moduleComments,
    $moduleQuiz,
    $myQuizAttempts,
    $quizSubmitResult,
    $selectedModulePending,
    $moduleContentsPending,
    $moduleAssignmentsPending,
    $moduleCommentsPending,
    $moduleQuizPending,
    $moduleContentCreatePending,
    $moduleLinkCreatePending,
    $moduleFileCreatePending,
    $moduleAssignmentCreatePending,
    $moduleAssignmentUpdatePending,
    $moduleAssignmentDeletePending,
    $moduleAssignmentAttachmentPending,
    $moduleAssignmentAttachmentClearPending,
    $assignmentSubmissionCreatePending,
    $assignmentSubmissionUpdatePending,
    $assignmentSubmissionDeletePending,
    $assignmentSubmissionGradePending,
    $moduleContentUpdatePending,
    $moduleContentReplacePending,
    $moduleContentDeletePending,
    $moduleCommentCreatePending,
    $moduleCommentDeletePending,
    $moduleQuizCreatePending,
    $moduleQuizUpdatePending,
    $moduleQuizDeletePending,
    $quizSubmitPending,
    modulePageOpened,
    modulePageReset,
    createModuleTextContentFx,
    createModuleLinkContentFx,
    uploadModuleFileContentFx,
    createModuleAssignmentFx,
    updateModuleAssignmentFx,
    deleteModuleAssignmentFx,
    uploadAssignmentAttachmentFx,
    clearAssignmentAttachmentFx,
    loadAssignmentSubmissionsFx,
    loadModuleFx,
    loadModuleAssignmentsFx,
    loadModuleAssignmentsQuietFx,
    loadModuleCommentsFx,
    loadModuleCommentsQuietFx,
    loadModuleContentsFx,
    loadModuleQuizFx,
    loadMyQuizAttemptsFx,
    createAssignmentSubmissionFx,
    updateAssignmentSubmissionFx,
    deleteAssignmentSubmissionFx,
    gradeAssignmentSubmissionFx,
    updateModuleContentFx,
    replaceModuleContentFileFx,
    deleteModuleContentFx,
    createModuleCommentFx,
    deleteModuleCommentFx,
    createModuleQuizFx,
    updateModuleQuizFx,
    deleteModuleQuizFx,
    submitQuizFx,
    loadCourseModulesFx,
    quizAttemptRestarted,
  ]);

  const [contentDrawerOpen, setContentDrawerOpen] = React.useState(false);
  const [assignmentDrawerOpen, setAssignmentDrawerOpen] = React.useState(false);
  const [submissionsDrawerOpen, setSubmissionsDrawerOpen] = React.useState(false);
  const [quizDrawerOpen, setQuizDrawerOpen] = React.useState(false);
  const [pendingContentFile, setPendingContentFile] = React.useState(null);
  const [pendingAssignmentFiles, setPendingAssignmentFiles] = React.useState([]);
  const [contentFileHint, setContentFileHint] = React.useState("");
  const [replyTarget, setReplyTarget] = React.useState(null);
  const [editingContent, setEditingContent] = React.useState(null);
  const [editingAssignment, setEditingAssignment] = React.useState(null);
  const [reviewAssignment, setReviewAssignment] = React.useState(null);
  const [editingQuiz, setEditingQuiz] = React.useState(false);
  const [deletingCommentId, setDeletingCommentId] = React.useState(null);
  const [deletingContentId, setDeletingContentId] = React.useState(null);
  const [deletingAssignmentId, setDeletingAssignmentId] = React.useState(null);
  const [reportModalOpen, setReportModalOpen] = React.useState(false);
  const [reportTargetComment, setReportTargetComment] = React.useState(null);
  const [reportSubmitting, setReportSubmitting] = React.useState(false);

  const contentFileInputRef = React.useRef(null);
  const assignmentFileInputRef = React.useRef(null);

  const [contentForm] = Form.useForm();
  const [assignmentForm] = Form.useForm();
  const [commentForm] = Form.useForm();
  const [quizForm] = Form.useForm();
  const [quizAnswerForm] = Form.useForm();
  const [reportForm] = Form.useForm();
  const contentType = Form.useWatch("content_type", contentForm);

  React.useEffect(() => {
    if (!moduleId) return undefined;
    openModulePage(moduleId);
    return () => resetModulePage();
  }, [moduleId, openModulePage, resetModulePage]);

  React.useEffect(() => {
    if (!module?.course_id) return;
    loadCourseModules(module.course_id).catch(() => {});
  }, [module?.course_id, loadCourseModules]);

  const isTeacher = user?.role === "teacher";
  const isAdmin = user?.role === "admin";
  const canManageModule = isAdmin || (isTeacher && myCourses.some((course) => course.id === module?.course_id));
  const allowedTabs = new Set(["content", "assignment", "quiz", "comments"]);
  const requestedTab = searchParams.get("tab");
  const activeStudentTab = allowedTabs.has(requestedTab) ? requestedTab : "content";
  const canTakeQuiz = Boolean(quiz?.id) && !canManageModule;
  const studentCourseModules = courseModules.filter((courseModule) => courseModule.is_published);
  const currentModuleIndex = studentCourseModules.findIndex((courseModule) => courseModule.id === module?.id);
  const previousModule = currentModuleIndex > 0 ? studentCourseModules[currentModuleIndex - 1] : null;
  const nextModule =
    currentModuleIndex >= 0 && currentModuleIndex < studentCourseModules.length - 1
      ? studentCourseModules[currentModuleIndex + 1]
      : null;
  const pendingSubmissionCount = assignments.reduce((total, assignment) => {
    const submissions = assignmentSubmissionsByAssignment[assignment.id] || [];
    return total + submissions.filter((submission) => submission.status !== "graded").length;
  }, 0);

  React.useEffect(() => {
    if (!canTakeQuiz || !quiz?.questions?.length) return;

    const existingAnswers = quizAnswerForm.getFieldsValue(true)?.answers || {};
    const nextAnswers = { ...existingAnswers };
    let changed = false;

    quiz.questions.forEach((question) => {
      if (!(question.id in nextAnswers)) {
        nextAnswers[question.id] = undefined;
        changed = true;
      }
    });

    if (changed) {
      quizAnswerForm.setFieldsValue({ answers: nextAnswers });
    }
  }, [canTakeQuiz, quiz?.id, quiz?.questions, quizAnswerForm]);

  React.useEffect(() => {
    if (!assignments.length) return;
    assignments.forEach((assignment) => {
      loadAssignmentSubmissions({ assignmentId: assignment.id, canManage: canManageModule }).catch(() => {});
    });
  }, [assignments, canManageModule, loadAssignmentSubmissions]);

  React.useEffect(() => {
    if (!moduleId || canManageModule) return undefined;

    let cancelled = false;

    const refreshStudentModuleState = () => {
      if (cancelled || document.visibilityState !== "visible") {
        return;
      }

      refreshModuleAssignmentsQuiet(moduleId)
        .then((nextAssignments) => {
          nextAssignments.forEach((assignment) => {
            loadAssignmentSubmissions({ assignmentId: assignment.id, canManage: false }).catch(() => {});
          });
        })
        .catch(() => {});
      refreshModuleCommentsQuiet(moduleId).catch(() => {});
    };

    const intervalId = window.setInterval(refreshStudentModuleState, STUDENT_MODULE_REFRESH_MS);
    const handleFocus = () => refreshStudentModuleState();
    const handleVisibilityChange = () => {
      if (document.visibilityState === "visible") {
        refreshStudentModuleState();
      }
    };

    window.addEventListener("focus", handleFocus);
    document.addEventListener("visibilitychange", handleVisibilityChange);

    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
      window.removeEventListener("focus", handleFocus);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, [
    canManageModule,
    loadAssignmentSubmissions,
    moduleId,
    refreshModuleAssignmentsQuiet,
    refreshModuleCommentsQuiet,
  ]);

  function resetContentFileInput() {
    if (contentFileInputRef.current) {
      contentFileInputRef.current.value = "";
    }
  }

  function resetAssignmentFileInput() {
    if (assignmentFileInputRef.current) {
      assignmentFileInputRef.current.value = "";
    }
  }

  function openContentDrawer(content = null) {
    setEditingContent(content);
    setPendingContentFile(null);
    setContentFileHint("");
    contentForm.setFieldsValue(
      content
        ? {
            content_type: content.content_type,
            title: content.title,
            text_content: content.text_content || "",
            source_url: content.source_url || "",
          }
        : defaultContentValues,
    );
    setContentDrawerOpen(true);
  }

  function closeContentDrawer() {
    setContentDrawerOpen(false);
    setEditingContent(null);
    setPendingContentFile(null);
    setContentFileHint("");
    contentForm.resetFields();
    resetContentFileInput();
  }

  function openAssignmentDrawer(assignment = null) {
    setEditingAssignment(assignment);
    setPendingAssignmentFiles([]);
    assignmentForm.setFieldsValue(
      assignment
        ? {
            title: assignment.title,
            instructions_markdown: assignment.instructions_markdown,
            max_score: assignment.max_score,
            due_at: toDateTimeLocalValue(assignment.due_at),
            is_published: assignment.is_published,
          }
        : defaultAssignmentValues,
    );
    setAssignmentDrawerOpen(true);
  }

  function closeAssignmentDrawer() {
    setAssignmentDrawerOpen(false);
    setEditingAssignment(null);
    setPendingAssignmentFiles([]);
    assignmentForm.resetFields();
    resetAssignmentFileInput();
  }

  function openSubmissionsDrawer(assignment) {
    setReviewAssignment(assignment);
    setSubmissionsDrawerOpen(true);
  }

  function closeSubmissionsDrawer() {
    setReviewAssignment(null);
    setSubmissionsDrawerOpen(false);
  }

  function openQuizDrawer(mode = "create") {
    const isEditMode = mode === "edit" && Boolean(quiz);
    setEditingQuiz(isEditMode);
    quizForm.setFieldsValue(
      isEditMode && quiz
        ? {
            title: quiz.title,
            due_at: toDateTimeLocalValue(quiz.due_at),
            is_published: quiz.is_published,
            questions: quiz.questions.map((question) => ({
              content: question.content,
              options: question.options,
              correct_option: question.correct_option || "",
              explanation: question.explanation || "",
            })),
          }
        : defaultQuizValues,
    );
    setQuizDrawerOpen(true);
  }

  function closeQuizDrawer() {
    setQuizDrawerOpen(false);
    setEditingQuiz(false);
    quizForm.resetFields();
  }

  function prepareContentFile(file) {
    if (!file) return;
    if (
      ![
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "video/mp4",
        "video/webm",
      ].includes(file.type)
    ) {
      message.error("Поддерживаются PDF, PPTX, MP4 и WEBM");
      return;
    }
    setPendingContentFile(file);
    setContentFileHint(file.name ? `Файл готов к загрузке: ${file.name}` : "Файл готов к загрузке");
  }

  function prepareAssignmentFiles(files) {
    setPendingAssignmentFiles(Array.from(files || []));
  }

  async function handleSaveContent(values) {
    if (!moduleId) return;
    try {
      if (editingContent) {
        const isFileContent = ["video", "pdf", "presentation"].includes(editingContent.content_type);

        if (isFileContent && pendingContentFile) {
          await submitContentFileReplace({
            contentId: editingContent.id,
            title: values.title,
            file: pendingContentFile,
          });
        } else {
          await submitContentUpdate({
            contentId: editingContent.id,
            payload: {
              title: values.title,
              text_content: values.content_type === "text" ? values.text_content : undefined,
              source_url: values.content_type === "link" ? values.source_url : undefined,
            },
          });
        }
      } else if (values.content_type === "text") {
        await submitTextContent({ moduleId, payload: { title: values.title, text_content: values.text_content } });
      } else if (values.content_type === "link") {
        await submitLinkContent({ moduleId, payload: { title: values.title, source_url: values.source_url } });
      } else {
        if (!pendingContentFile) {
          message.error("Выберите файл для загрузки");
          return;
        }
        await submitFileContent({
          moduleId,
          title: values.title,
          file: pendingContentFile,
          contentType: values.content_type,
        });
      }
      message.success(editingContent ? "Материал обновлен" : "Контент модуля добавлен");
      closeContentDrawer();
    } catch (error) {
      message.error(getErrorMessage(error, "Не удалось сохранить контент"));
    }
  }

  async function handleSaveAssignment(values) {
    if (!moduleId) return;
    try {
      const payload = { ...values, due_at: fromDateTimeLocalValue(values.due_at) };
      const assignmentRecord = editingAssignment
        ? await submitUpdateAssignment({ assignmentId: editingAssignment.id, payload })
        : await submitCreateAssignment({ moduleId, payload });

      if (pendingAssignmentFiles.length && assignmentRecord?.id) {
        await submitUploadAssignmentAttachment({ assignmentId: assignmentRecord.id, files: pendingAssignmentFiles });
      }

      message.success(editingAssignment ? "Задание обновлено" : "Задание создано");
      closeAssignmentDrawer();
    } catch (error) {
      message.error(getErrorMessage(error, "Не удалось сохранить задание"));
    }
  }

  async function handleDeleteContent(content) {
    if (!moduleId) return;
    try {
      setDeletingContentId(content.id);
      await submitContentDelete({ contentId: content.id, moduleId });
      message.success("Материал удален");
    } catch (error) {
      message.error(getErrorMessage(error, "Не удалось удалить материал"));
    } finally {
      setDeletingContentId(null);
    }
  }

  async function handleDeleteAssignment(assignment) {
    if (!moduleId) return;
    try {
      setDeletingAssignmentId(assignment.id);
      await submitDeleteAssignment({ assignmentId: assignment.id, moduleId });
      message.success("Задание удалено");
    } catch (error) {
      message.error(getErrorMessage(error, "Не удалось удалить задание"));
    } finally {
      setDeletingAssignmentId(null);
    }
  }

  async function handleStudentAssignmentSubmit(assignment, payload) {
    await submitAssignmentSubmission({
      assignmentId: assignment.id,
      answerMarkdown: payload.answerMarkdown,
      files: payload.files,
    });
    loadAssignmentSubmissions({ assignmentId: assignment.id, canManage: false }).catch(() => {});
  }

  async function handleStudentAssignmentUpdate(submission, payload) {
    await submitAssignmentSubmissionUpdate({
      submissionId: submission.id,
      answerMarkdown: payload.answerMarkdown,
      files: payload.files,
    });
    loadAssignmentSubmissions({ assignmentId: submission.assignment_id, canManage: false }).catch(() => {});
  }

  async function handleStudentAssignmentDelete(submission) {
    await submitAssignmentSubmissionDelete({
      submissionId: submission.id,
      assignmentId: submission.assignment_id,
    });
    loadAssignmentSubmissions({ assignmentId: submission.assignment_id, canManage: false }).catch(() => {});
  }

  async function handleCreateComment(values) {
    if (!moduleId) return;
    try {
      await submitComment({
        moduleId,
        payload: {
          content: values.content,
          parent_comment_id: replyTarget?.id || null,
        },
      });
      message.success(replyTarget ? "Ответ отправлен" : "Комментарий отправлен");
      commentForm.resetFields();
      setReplyTarget(null);
    } catch (error) {
      message.error(getErrorMessage(error, "Не удалось отправить комментарий"));
    }
  }

  async function handleDeleteComment(comment) {
    if (!moduleId) return;
    try {
      setDeletingCommentId(comment.id);
      await submitCommentDelete({ commentId: comment.id, moduleId });
      message.success("Комментарий удален");
      if (replyTarget?.id === comment.id) {
        setReplyTarget(null);
      }
    } catch (error) {
      message.error(getErrorMessage(error, "Не удалось удалить комментарий"));
    } finally {
      setDeletingCommentId(null);
    }
  }

  async function handleClearAssignmentAttachments() {
    if (!editingAssignment?.id) return;
    try {
      const assignmentRecord = await submitClearAssignmentAttachment({ assignmentId: editingAssignment.id });
      setEditingAssignment(assignmentRecord);
      setPendingAssignmentFiles([]);
      resetAssignmentFileInput();
      message.success("Файлы задания удалены");
    } catch (error) {
      message.error(getErrorMessage(error, "Не удалось удалить файлы задания"));
    }
  }

  function handleReportComment(comment) {
    setReportTargetComment(comment);
    reportForm.setFieldsValue({
      category: "abuse",
      reason: "Оскорбление, спам или неуместный контент",
      details: "",
    });
    setReportModalOpen(true);
  }

  async function submitCommentReport() {
    if (!reportTargetComment) return;
    try {
      const values = await reportForm.validateFields();
      setReportSubmitting(true);
      await createReport({
        target_type: "comment",
        comment_id: reportTargetComment.id,
        reason: values.reason,
        category: values.category,
        details: values.details || null,
      });
      message.success("Жалоба отправлена модератору");
      setReportModalOpen(false);
      setReportTargetComment(null);
      reportForm.resetFields();
    } catch (error) {
      message.error(getErrorMessage(error, "Не удалось отправить жалобу"));
    } finally {
      setReportSubmitting(false);
    }
  }

  async function handleSaveQuiz(values) {
    if (!moduleId) return;
    try {
      const payload = {
        title: values.title,
        due_at: fromDateTimeLocalValue(values.due_at),
        is_published: values.is_published,
        questions: (values.questions || []).map((question, questionIndex) => ({
          content: question.content,
          options: (question.options || []).filter((option) => option && option.trim().length > 0),
          correct_option: question.correct_option,
          explanation: question.explanation || null,
          position: questionIndex + 1,
        })),
      };

      if (editingQuiz && quiz?.id) {
        await submitQuizUpdate({ quizId: quiz.id, payload });
      } else {
        await submitCreateQuiz({ moduleId, payload });
      }
      message.success(editingQuiz ? "Квиз обновлен" : "Квиз создан");
      closeQuizDrawer();
    } catch (error) {
      message.error(getErrorMessage(error, "Не удалось сохранить квиз"));
    }
  }

  async function handleDeleteQuiz() {
    if (!moduleId || !quiz?.id) return;
    try {
      await submitQuizDelete({ quizId: quiz.id, moduleId });
      message.success("Квиз удален");
    } catch (error) {
      message.error(getErrorMessage(error, "Не удалось удалить квиз"));
    }
  }

  async function handleSubmitQuiz(values) {
    if (!quiz?.id) return;
    try {
      const payload = {
        answers: quiz.questions.map((question) => ({
          question_id: question.id,
          selected_option: values.answers?.[question.id],
        })),
      };
      await submitQuizAttempt({ quizId: quiz.id, payload });
      message.success("Попытка сохранена");
    } catch (error) {
      message.error(getErrorMessage(error, "Не удалось отправить ответы"));
    }
  }

  async function handleGradeSubmission(submission, values) {
    try {
      await submitGradeAssignmentSubmission({ submissionId: submission.id, payload: values });
      loadAssignmentSubmissions({ assignmentId: submission.assignment_id, canManage: true }).catch(() => {});
      message.success("Оценка сохранена");
    } catch (error) {
      message.error(getErrorMessage(error, "Не удалось сохранить оценку"));
    }
  }

  function handleRestartQuizAttempt() {
    if (!quiz?.questions?.length) return;
    const answers = {};
    quiz.questions.forEach((question) => {
      answers[question.id] = undefined;
    });
    quizAnswerForm.setFieldsValue({ answers });
    restartQuizAttempt();
    message.info("Можно начать новую попытку");
  }

  function handleStudentTabChange(tabKey) {
    const nextParams = new URLSearchParams(searchParams);
    nextParams.set("tab", tabKey);
    setSearchParams(nextParams, { replace: true });
  }

  if (modulePending && !module) {
    return <ModuleLoadingState />;
  }

  if (!module && !modulePending) {
    return <ModuleNotFoundState onBack={() => navigate("/courses")} />;
  }

  return (
    <AppShell
      title={module?.title || "Модуль"}
      subtitle={
        canManageModule
          ? "Собирайте материалы, задания, обсуждение и проверку знаний прямо внутри одного модуля."
          : "Проходите модуль по шагам: изучайте материал, выполняйте задание, проходите тест и обсуждайте тему."
      }
    >
      <PageBreadcrumbs
        items={[
          { label: "Главная", href: "/dashboard" },
          { label: "Каталог курсов", href: "/courses" },
          { label: module?.course_title || "Курс", href: `/courses/${module?.course_id}` },
          { label: module?.title || "Модуль" },
        ]}
      />

      <Row gutter={[20, 20]}>
        {canManageModule ? (
          <>
            <Col xs={24}>
              <TeacherModuleOverviewCard
                module={module}
                contentCount={contents.length}
                assignmentCount={assignments.length}
                hasQuiz={Boolean(quiz?.id)}
                pendingSubmissionCount={pendingSubmissionCount}
                onAddContent={() => openContentDrawer()}
                onAddAssignment={() => openAssignmentDrawer()}
                onAddQuiz={() => openQuizDrawer(quiz ? "edit" : "create")}
              />
            </Col>

            <Col xs={24}>
              <TeacherModuleWorkspace
                contents={contents}
                contentsPending={contentsPending}
                deletingContentId={deletingContentId}
                onDeleteContent={handleDeleteContent}
                onEditContent={openContentDrawer}
                onOpenContentDrawer={() => openContentDrawer()}
                assignments={assignments}
                submissionsByAssignment={assignmentSubmissionsByAssignment}
                assignmentsPending={assignmentsPending}
                assignmentSaving={creatingAssignment || updatingAssignment || uploadingAssignmentAttachment || clearingAssignmentAttachment}
                assignmentDeletingId={deletingAssignmentId}
                submissionPending={creatingAssignmentSubmission || updatingAssignmentSubmission || deletingAssignmentSubmission}
                submissionUpdating={updatingAssignmentSubmission}
                submissionDeleting={deletingAssignmentSubmission}
                gradingPending={gradingAssignmentSubmission}
                onOpenAssignmentDrawer={openAssignmentDrawer}
                onDeleteAssignment={handleDeleteAssignment}
                onOpenSubmissionsDrawer={openSubmissionsDrawer}
                onStudentSubmit={handleStudentAssignmentSubmit}
                onStudentUpdate={handleStudentAssignmentUpdate}
                onStudentDelete={handleStudentAssignmentDelete}
                comments={comments}
                commentsPending={commentsPending}
                commentForm={commentForm}
                creatingComment={creatingComment}
                deletingCommentId={deletingCommentId}
                currentUserId={user?.id}
                replyTarget={replyTarget}
                onCancelReply={() => setReplyTarget(null)}
                onDeleteComment={handleDeleteComment}
                onSubmitComment={handleCreateComment}
                onReply={setReplyTarget}
                onReportComment={handleReportComment}
                quiz={quiz}
                quizPending={quizPending}
                attempts={attempts}
                quizSubmitResult={quizSubmitResult}
                submittingQuiz={submittingQuiz}
                deletingQuiz={deletingQuiz}
                quizAnswerForm={quizAnswerForm}
                onDeleteQuiz={handleDeleteQuiz}
                onEditQuiz={() => openQuizDrawer("edit")}
                onSubmitQuiz={handleSubmitQuiz}
                onRestartAttempt={handleRestartQuizAttempt}
                onOpenQuizDrawer={() => openQuizDrawer("create")}
                pendingSubmissionCount={pendingSubmissionCount}
              />
            </Col>
          </>
        ) : (
          <Col xs={24}>
            <StudentModuleWorkspace
              module={module}
              courseModules={studentCourseModules}
              contents={contents}
              contentsPending={contentsPending}
              assignments={assignments}
              assignmentSubmissionsByAssignment={assignmentSubmissionsByAssignment}
              assignmentsPending={assignmentsPending}
              assignmentSubmissionPending={creatingAssignmentSubmission || updatingAssignmentSubmission || deletingAssignmentSubmission}
              assignmentSubmissionUpdating={updatingAssignmentSubmission}
              assignmentSubmissionDeleting={deletingAssignmentSubmission}
              comments={comments}
              commentsPending={commentsPending}
              commentForm={commentForm}
              creatingComment={creatingComment}
              deletingCommentId={deletingCommentId}
              currentUserId={user?.id}
              replyTarget={replyTarget}
              onCancelReply={() => setReplyTarget(null)}
              onCommentDelete={handleDeleteComment}
              onCommentSubmit={handleCreateComment}
              onReply={setReplyTarget}
              onReportComment={handleReportComment}
              onStudentAssignmentSubmit={handleStudentAssignmentSubmit}
              onStudentAssignmentUpdate={handleStudentAssignmentUpdate}
              onStudentAssignmentDelete={handleStudentAssignmentDelete}
              quiz={quiz}
              quizPending={quizPending}
              canTakeQuiz={canTakeQuiz}
              attempts={attempts}
              quizSubmitResult={quizSubmitResult}
              submittingQuiz={submittingQuiz}
              quizAnswerForm={quizAnswerForm}
              onSubmitQuiz={handleSubmitQuiz}
              onRestartAttempt={handleRestartQuizAttempt}
              previousModule={previousModule}
              nextModule={nextModule}
              activeTab={activeStudentTab}
              onTabChange={handleStudentTabChange}
            />
          </Col>
        )}
      </Row>

      <ModuleManagementDrawers
        contentDrawerOpen={contentDrawerOpen}
        contentForm={contentForm}
        contentType={contentType}
        contentFileHint={contentFileHint}
        editingContent={editingContent}
        replacingContentFile={replacingContentFile}
        savingContent={creatingText || creatingLink || uploadingFile || updatingContent}
        contentFileInputRef={contentFileInputRef}
        onCloseContentDrawer={closeContentDrawer}
        onSaveContent={handleSaveContent}
        onPrepareContentFile={prepareContentFile}
        assignmentDrawerOpen={assignmentDrawerOpen}
        assignmentForm={assignmentForm}
        editingAssignment={editingAssignment}
        assignmentSaving={creatingAssignment || updatingAssignment || uploadingAssignmentAttachment || clearingAssignmentAttachment}
        pendingAssignmentFiles={pendingAssignmentFiles}
        assignmentFileInputRef={assignmentFileInputRef}
        onCloseAssignmentDrawer={closeAssignmentDrawer}
        onSaveAssignment={handleSaveAssignment}
        onPrepareAssignmentFiles={prepareAssignmentFiles}
        onClearAssignmentAttachments={handleClearAssignmentAttachments}
        clearingAssignmentAttachments={clearingAssignmentAttachment}
        submissionsDrawerOpen={submissionsDrawerOpen}
        reviewAssignment={reviewAssignment}
        assignmentSubmissions={reviewAssignment ? assignmentSubmissionsByAssignment[reviewAssignment.id] || [] : []}
        gradingAssignmentSubmission={gradingAssignmentSubmission}
        onCloseSubmissionsDrawer={closeSubmissionsDrawer}
        onGradeSubmission={handleGradeSubmission}
        quizDrawerOpen={quizDrawerOpen}
        quizForm={quizForm}
        savingQuiz={creatingQuiz || updatingQuiz}
        editingQuiz={editingQuiz}
        questionsLocked={Boolean(editingQuiz && quiz?.has_attempts)}
        onCloseQuizDrawer={closeQuizDrawer}
        onSaveQuiz={handleSaveQuiz}
      />
      <Modal
        title="Пожаловаться на комментарий"
        open={reportModalOpen}
        okText="Отправить жалобу"
        cancelText="Отмена"
        confirmLoading={reportSubmitting}
        onOk={submitCommentReport}
        onCancel={() => {
          setReportModalOpen(false);
          setReportTargetComment(null);
          reportForm.resetFields();
        }}
      >
        <Form form={reportForm} layout="vertical">
          <Form.Item name="category" label="Категория" rules={[{ required: true, message: "Выберите категорию" }]}>
            <Select
              options={[
                { value: "abuse", label: "Оскорбления/токсичность" },
                { value: "spam", label: "Спам" },
                { value: "misinformation", label: "Недостоверный контент" },
                { value: "offtopic", label: "Не по теме" },
                { value: "other", label: "Другое" },
              ]}
            />
          </Form.Item>
          <Form.Item name="reason" label="Причина" rules={[{ required: true, message: "Укажите причину" }]}>
            <Input />
          </Form.Item>
          <Form.Item name="details" label="Детали (необязательно)">
            <Input.TextArea rows={4} />
          </Form.Item>
        </Form>
      </Modal>
    </AppShell>
  );
}
