import React from "react";
import { Badge, Segmented, Space, Tabs, Typography } from "antd";

import { ModuleAssignmentsPanel } from "./ModuleAssignmentsPanel";
import { ModuleCommentsPanel } from "./ModuleCommentsPanel";
import { ModuleContentPanel } from "./ModuleContentPanel";
import { ModuleQuizPanel } from "./ModuleQuizPanel";

export function TeacherModuleWorkspace({
  contents,
  contentsPending,
  deletingContentId,
  onDeleteContent,
  onEditContent,
  onOpenContentDrawer,
  assignments,
  submissionsByAssignment,
  assignmentsPending,
  assignmentSaving,
  assignmentDeletingId,
  submissionPending,
  submissionUpdating,
  submissionDeleting,
  gradingPending,
  onOpenAssignmentDrawer,
  onDeleteAssignment,
  onOpenSubmissionsDrawer,
  onStudentSubmit,
  onStudentUpdate,
  onStudentDelete,
  comments,
  commentsPending,
  commentForm,
  creatingComment,
  deletingCommentId,
  currentUserId,
  replyTarget,
  onCancelReply,
  onDeleteComment,
  onSubmitComment,
  onReply,
  onReportComment,
  quiz,
  quizPending,
  attempts,
  quizSubmitResult,
  submittingQuiz,
  deletingQuiz,
  quizAnswerForm,
  onDeleteQuiz,
  onEditQuiz,
  onSubmitQuiz,
  onRestartAttempt,
  onOpenQuizDrawer,
  pendingSubmissionCount,
}) {
  const [activeTab, setActiveTab] = React.useState("content");

  const tabItems = [
    {
      key: "content",
      label: "Материалы",
      children: (
        <ModuleContentPanel
          contents={contents}
          contentsPending={contentsPending}
          canManageModule
          deletingContentId={deletingContentId}
          onDeleteContent={onDeleteContent}
          onEditContent={onEditContent}
          onOpenContentDrawer={onOpenContentDrawer}
        />
      ),
    },
    {
      key: "assignments",
      label: pendingSubmissionCount > 0 ? <Badge count={pendingSubmissionCount} size="small">Задания</Badge> : "Задания",
      children: (
        <ModuleAssignmentsPanel
          assignments={assignments}
          submissionsByAssignment={submissionsByAssignment}
          assignmentsPending={assignmentsPending}
          canManageModule
          assignmentSaving={assignmentSaving}
          assignmentDeletingId={assignmentDeletingId}
          submissionPending={submissionPending}
          submissionUpdating={submissionUpdating}
          submissionDeleting={submissionDeleting}
          gradingPending={gradingPending}
          onOpenAssignmentDrawer={onOpenAssignmentDrawer}
          onDeleteAssignment={onDeleteAssignment}
          onOpenSubmissionsDrawer={onOpenSubmissionsDrawer}
          onStudentSubmit={onStudentSubmit}
          onStudentUpdate={onStudentUpdate}
          onStudentDelete={onStudentDelete}
        />
      ),
    },
    {
      key: "quiz",
      label: "Тест",
      children: (
        <ModuleQuizPanel
          quiz={quiz}
          quizPending={quizPending}
          canManageModule
          canTakeQuiz={false}
          attempts={attempts}
          quizSubmitResult={quizSubmitResult}
          submittingQuiz={submittingQuiz}
          deletingQuiz={deletingQuiz}
          quizAnswerForm={quizAnswerForm}
          onDeleteQuiz={onDeleteQuiz}
          onEditQuiz={onEditQuiz}
          onSubmitQuiz={onSubmitQuiz}
          onRestartAttempt={onRestartAttempt}
          onOpenQuizDrawer={onOpenQuizDrawer}
        />
      ),
    },
    {
      key: "comments",
      label: "Обсуждение",
      children: (
        <ModuleCommentsPanel
          comments={comments}
          commentsPending={commentsPending}
          commentForm={commentForm}
          creatingComment={creatingComment}
          deletingCommentId={deletingCommentId}
          currentUserId={currentUserId}
          replyTarget={replyTarget}
          onCancelReply={onCancelReply}
          onDelete={onDeleteComment}
          onSubmit={onSubmitComment}
          onReply={onReply}
          onReport={onReportComment}
        />
      ),
    },
  ];

  return (
    <Space direction="vertical" size={20} className="module-main-stack teacher-module-workspace">
      <div className="teacher-workspace-head">
        <div>
          <Typography.Title level={4} className="teacher-workspace-title">
            Рабочая область преподавателя
          </Typography.Title>
          <Typography.Text className="teacher-workspace-copy">
            Управляйте модулем по секциям: материалы, задания, тест и обсуждение собраны в отдельные рабочие зоны.
          </Typography.Text>
        </div>

        <Segmented
          value={activeTab}
          onChange={setActiveTab}
          options={[
            { label: "Материалы", value: "content" },
            { label: "Задания", value: "assignments" },
            { label: "Тест", value: "quiz" },
            { label: "Обсуждение", value: "comments" },
          ]}
        />
      </div>

      <Tabs activeKey={activeTab} onChange={setActiveTab} items={tabItems} className="teacher-module-tabs" />
    </Space>
  );
}
