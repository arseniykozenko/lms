import React from "react";
import { LeftOutlined, MenuOutlined, RightOutlined } from "@ant-design/icons";
import { Button, Card, Space, Tabs, Tag, Typography } from "antd";
import { Link } from "react-router-dom";

import { ModuleCommentsPanel } from "./ModuleCommentsPanel";
import { ModuleAssignmentsPanel } from "./ModuleAssignmentsPanel";
import { ModuleNavigatorDrawer } from "./ModuleNavigatorDrawer";
import { ModuleQuizPanel } from "./ModuleQuizPanel";
import { StudentContentWorkspace } from "./StudentContentWorkspace";

export function StudentModuleWorkspace({
  module,
  courseModules,
  contents,
  contentsPending,
  assignments,
  assignmentSubmissionsByAssignment,
  assignmentsPending,
  assignmentSubmissionPending,
  assignmentSubmissionUpdating,
  assignmentSubmissionDeleting,
  comments,
  commentsPending,
  commentForm,
  creatingComment,
  deletingCommentId,
  currentUserId,
  replyTarget,
  onCancelReply,
  onCommentDelete,
  onCommentSubmit,
  onReply,
  onReportComment,
  onStudentAssignmentSubmit,
  onStudentAssignmentUpdate,
  onStudentAssignmentDelete,
  quiz,
  quizPending,
  canTakeQuiz,
  attempts,
  quizSubmitResult,
  submittingQuiz,
  quizAnswerForm,
  onSubmitQuiz,
  onRestartAttempt,
  previousModule,
  nextModule,
  activeTab = "content",
  onTabChange = () => {},
}) {
  const [navOpen, setNavOpen] = React.useState(false);

  const tabItems = [
    {
      key: "content",
      label: "Материал",
      children: <StudentContentWorkspace moduleId={module?.id} contents={contents} />,
    },
    {
      key: "assignment",
      label: "Задание",
      children: (
        <ModuleAssignmentsPanel
          assignments={assignments}
          submissionsByAssignment={assignmentSubmissionsByAssignment}
          assignmentsPending={assignmentsPending}
          canManageModule={false}
          assignmentDeletingId={null}
          submissionPending={assignmentSubmissionPending}
          submissionUpdating={assignmentSubmissionUpdating}
          submissionDeleting={assignmentSubmissionDeleting}
          onOpenAssignmentDrawer={() => {}}
          onDeleteAssignment={() => {}}
          onOpenSubmissionsDrawer={() => {}}
          onStudentSubmit={onStudentAssignmentSubmit}
          onStudentUpdate={onStudentAssignmentUpdate}
          onStudentDelete={onStudentAssignmentDelete}
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
          canManageModule={false}
          canTakeQuiz={canTakeQuiz}
          attempts={attempts}
          quizSubmitResult={quizSubmitResult}
          submittingQuiz={submittingQuiz}
          deletingQuiz={false}
          quizAnswerForm={quizAnswerForm}
          onDeleteQuiz={() => {}}
          onEditQuiz={() => {}}
          onSubmitQuiz={onSubmitQuiz}
          onRestartAttempt={onRestartAttempt}
          onOpenQuizDrawer={() => {}}
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
          onDelete={onCommentDelete}
          onSubmit={onCommentSubmit}
          onReply={onReply}
          onReport={onReportComment}
        />
      ),
    },
  ];

  return (
    <div className="student-module-stack">
      <Card className="panel-card student-module-header-card">
        <div className="student-module-header">
          <div className="student-module-header-copy">
            <Space className="course-card-tags" wrap>
              <Tag color="blue">Модуль {module?.position}</Tag>
              <Tag color={module?.is_published ? "green" : "orange"}>
                {module?.is_published ? "Открыт" : "Черновик"}
              </Tag>
            </Space>
            <Typography.Title level={3} className="student-module-title">
              {module?.title}
            </Typography.Title>
            <Typography.Paragraph className="panel-copy student-module-copy">
              {module?.description || "Описание модуля пока не добавлено."}
            </Typography.Paragraph>
          </div>

          <div className="student-module-topnav">
            <Button icon={<MenuOutlined />} onClick={() => setNavOpen(true)}>
              Навигация
            </Button>
            <Button disabled={!previousModule} icon={<LeftOutlined />}>
              {previousModule ? <Link to={`/modules/${previousModule.id}`}>Назад</Link> : "Назад"}
            </Button>
            <Button>
              <Link to={`/courses/${module?.course_id}`}>К курсу</Link>
            </Button>
            <Button type="primary" disabled={!nextModule} icon={<RightOutlined />} iconPosition="end">
              {nextModule ? <Link to={`/modules/${nextModule.id}`}>Далее</Link> : "Далее"}
            </Button>
          </div>
        </div>
      </Card>

      <ModuleNavigatorDrawer
        open={navOpen}
        onClose={() => setNavOpen(false)}
        modules={courseModules}
        currentModuleId={module?.id}
        contents={contents}
        moduleBaseRoute={module?.id ? `/modules/${module.id}` : null}
        activeModuleTab={activeTab}
      />

      <Card className="panel-card student-module-tabs-card">
        <Tabs activeKey={activeTab} onChange={onTabChange} items={tabItems} />
      </Card>
    </div>
  );
}
