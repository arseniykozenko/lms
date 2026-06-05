import React from "react";

import { AssignmentEditorDrawer } from "./AssignmentEditorDrawer";
import { AssignmentSubmissionsDrawer } from "./AssignmentSubmissionsDrawer";
import { ModuleContentDrawer } from "./ModuleContentDrawer";
import { ModuleQuizDrawer } from "./ModuleQuizDrawer";

const defaultContentValues = {
  content_type: "text",
  title: "",
  text_content: "",
  source_url: "",
};

const defaultQuizValues = {
  title: "",
  is_published: true,
  questions: [{ content: "", options: ["", ""], correct_option: "", explanation: "" }],
};

export function ModuleManagementDrawers({
  contentDrawerOpen,
  contentForm,
  contentType,
  contentFileHint,
  editingContent,
  replacingContentFile,
  savingContent,
  contentFileInputRef,
  onCloseContentDrawer,
  onSaveContent,
  onPrepareContentFile,
  assignmentDrawerOpen,
  assignmentForm,
  editingAssignment,
  assignmentSaving,
  pendingAssignmentFiles,
  assignmentFileInputRef,
  onCloseAssignmentDrawer,
  onSaveAssignment,
  onPrepareAssignmentFiles,
  onClearAssignmentAttachments,
  clearingAssignmentAttachments,
  submissionsDrawerOpen,
  reviewAssignment,
  assignmentSubmissions,
  gradingAssignmentSubmission,
  onCloseSubmissionsDrawer,
  onGradeSubmission,
  quizDrawerOpen,
  quizForm,
  savingQuiz,
  editingQuiz,
  questionsLocked,
  onCloseQuizDrawer,
  onSaveQuiz,
}) {
  return (
    <>
      <ModuleContentDrawer
        open={contentDrawerOpen}
        form={contentForm}
        defaultValues={defaultContentValues}
        contentType={contentType}
        fileHint={contentFileHint}
        isEditing={Boolean(editingContent)}
        replacingFile={replacingContentFile}
        savingContent={savingContent}
        fileInputRef={contentFileInputRef}
        onClose={onCloseContentDrawer}
        onSubmit={onSaveContent}
        onPrepareFile={onPrepareContentFile}
      />

      <AssignmentEditorDrawer
        open={assignmentDrawerOpen}
        form={assignmentForm}
        isEditing={Boolean(editingAssignment)}
        saving={assignmentSaving}
        attachments={editingAssignment?.attachments || []}
        selectedFiles={pendingAssignmentFiles}
        fileInputRef={assignmentFileInputRef}
        onClose={onCloseAssignmentDrawer}
        onSubmit={onSaveAssignment}
        onPrepareFiles={onPrepareAssignmentFiles}
        onClearAttachments={onClearAssignmentAttachments}
        clearingAttachments={clearingAssignmentAttachments}
      />

      <AssignmentSubmissionsDrawer
        open={submissionsDrawerOpen}
        assignment={reviewAssignment}
        submissions={assignmentSubmissions}
        gradingPending={gradingAssignmentSubmission}
        onClose={onCloseSubmissionsDrawer}
        onGrade={onGradeSubmission}
      />

      <ModuleQuizDrawer
        open={quizDrawerOpen}
        form={quizForm}
        defaultValues={defaultQuizValues}
        savingQuiz={savingQuiz}
        isEditing={editingQuiz}
        questionsLocked={questionsLocked}
        onClose={onCloseQuizDrawer}
        onSubmit={onSaveQuiz}
      />
    </>
  );
}
