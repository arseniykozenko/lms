import React from "react";
import { FileAddOutlined } from "@ant-design/icons";
import {
  Alert,
  Button,
  Card,
  Descriptions,
  Empty,
  List,
  Popconfirm,
  Skeleton,
  Space,
  Tag,
  Typography,
  message,
} from "antd";

import { AttachmentList } from "../shared/AttachmentList";
import { MarkdownContent } from "../shared/MarkdownContent";
import { MarkdownEditor } from "../shared/MarkdownEditor";
import { formatDate } from "./moduleHelpers";

const supportedSubmissionExtensions = new Set([".pdf", ".zip", ".rar", ".7z", ".pptx", ".doc", ".docx", ".txt"]);
const supportedSubmissionTypes = new Set([
  "application/pdf",
  "application/zip",
  "application/x-zip-compressed",
  "application/x-rar-compressed",
  "application/vnd.rar",
  "application/x-7z-compressed",
  "application/vnd.openxmlformats-officedocument.presentationml.presentation",
  "application/msword",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "text/plain",
]);

export function ModuleAssignmentsPanel({
  assignments,
  submissionsByAssignment,
  assignmentsPending,
  canManageModule,
  assignmentDeletingId,
  submissionPending,
  submissionUpdating,
  submissionDeleting,
  onOpenAssignmentDrawer,
  onDeleteAssignment,
  onOpenSubmissionsDrawer,
  onStudentSubmit,
  onStudentUpdate,
  onStudentDelete,
}) {
  if (assignmentsPending && assignments.length === 0) {
    return (
      <Card className="panel-card" title="Задания">
        <Skeleton active paragraph={{ rows: 6 }} />
      </Card>
    );
  }

  return (
    <Card
      className="panel-card"
      title={
        <Space>
          <FileAddOutlined />
          <span>Задания</span>
        </Space>
      }
      extra={
        canManageModule ? (
          <Button type="link" onClick={() => onOpenAssignmentDrawer(null)}>
            Добавить задание
          </Button>
        ) : null
      }
    >
      <Typography.Paragraph className="panel-copy">
        {canManageModule
          ? "Здесь преподаватель задает практическую работу, прикладывает материалы и проверяет ответы студентов."
          : "Прочитайте условие, изучите материалы и отправьте один актуальный ответ. После отправки его можно редактировать или удалить."}
      </Typography.Paragraph>

      {assignments.length === 0 ? (
        <Empty
          description={
            canManageModule
              ? "Пока заданий нет. Добавьте первое практическое задание."
              : "Для этого модуля пока нет заданий."
          }
        />
      ) : (
        <List
          dataSource={assignments}
          renderItem={(assignment) => (
            <List.Item key={assignment.id} className="assignment-list-item">
              {canManageModule ? (
                <TeacherAssignmentCard
                  assignment={assignment}
                  submissions={submissionsByAssignment[assignment.id] || []}
                  isDeleting={assignmentDeletingId === assignment.id}
                  onDelete={() => onDeleteAssignment(assignment)}
                  onEdit={() => onOpenAssignmentDrawer(assignment)}
                  onOpenSubmissions={() => onOpenSubmissionsDrawer(assignment)}
                />
              ) : (
                <StudentAssignmentCard
                  assignment={assignment}
                  submissions={submissionsByAssignment[assignment.id] || []}
                  submissionPending={submissionPending}
                  submissionUpdating={submissionUpdating}
                  submissionDeleting={submissionDeleting}
                  onSubmit={(payload) => onStudentSubmit(assignment, payload)}
                  onUpdate={onStudentUpdate}
                  onDelete={onStudentDelete}
                />
              )}
            </List.Item>
          )}
        />
      )}
    </Card>
  );
}

function TeacherAssignmentCard({ assignment, submissions, isDeleting, onDelete, onEdit, onOpenSubmissions }) {
  return (
    <Card className="assignment-card">
      <div className="assignment-card-head">
        <div>
          <Space wrap>
            <Typography.Title level={4} className="assignment-title">
              {assignment.title}
            </Typography.Title>
            <Tag color={assignment.is_published ? "green" : "orange"}>
              {assignment.is_published ? "Опубликовано" : "Черновик"}
            </Tag>
            {assignment.max_score != null ? <Tag color="gold">До {assignment.max_score} баллов</Tag> : null}
          </Space>
          <Typography.Text type="secondary">
            {assignment.has_submissions ? `Есть ответы студентов: ${submissions.length}` : "Ответов пока нет"}
          </Typography.Text>
        </div>

        <Space wrap>
          <Button onClick={onOpenSubmissions}>Ответы</Button>
          <Button onClick={onEdit}>Изменить</Button>
          <Popconfirm
            title="Удалить задание?"
            description="Задание и ответы на него будут удалены."
            okText="Удалить"
            cancelText="Отмена"
            onConfirm={onDelete}
          >
            <Button danger loading={isDeleting}>
              Удалить
            </Button>
          </Popconfirm>
        </Space>
      </div>

      <div className="assignment-markdown-card">
        <MarkdownContent value={assignment.instructions_markdown} />
      </div>

      {(assignment.attachments || []).length ? (
        <div className="assignment-attachment-row">
          <Typography.Text strong>Приложенные файлы:</Typography.Text>
          <AttachmentList attachments={assignment.attachments} />
        </div>
      ) : null}
    </Card>
  );
}

function StudentAssignmentCard({
  assignment,
  submissions,
  submissionPending,
  submissionUpdating,
  submissionDeleting,
  onSubmit,
  onUpdate,
  onDelete,
}) {
  const currentSubmission = submissions[0] || null;
  const [isEditing, setIsEditing] = React.useState(false);
  const [answer, setAnswer] = React.useState("");
  const [files, setFiles] = React.useState([]);
  const fileInputRef = React.useRef(null);

  React.useEffect(() => {
    if (!currentSubmission || isEditing) return;
    setAnswer(currentSubmission.answer_markdown || "");
    setFiles([]);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }, [currentSubmission, isEditing]);

  function resetDraft() {
    setAnswer(currentSubmission?.answer_markdown || "");
    setFiles([]);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }

  function handlePickFiles(nextFiles) {
    const resolvedFiles = Array.from(nextFiles || []);
    if (!resolvedFiles.length) {
      setFiles([]);
      return;
    }

    for (const nextFile of resolvedFiles) {
      const extension = `.${(nextFile.name.split(".").pop() || "").toLowerCase()}`;
      const isMimeSupported = nextFile.type ? supportedSubmissionTypes.has(nextFile.type) : false;
      const isExtensionSupported = supportedSubmissionExtensions.has(extension);

      if (!isMimeSupported && !isExtensionSupported) {
        message.error("Поддерживаются PDF, ZIP, RAR, 7Z, PPTX, DOC, DOCX и TXT");
        if (fileInputRef.current) {
          fileInputRef.current.value = "";
        }
        setFiles([]);
        return;
      }
    }

    setFiles(resolvedFiles);
  }

  async function handleCreate() {
    if (!answer.trim() && files.length === 0) {
      message.warning("Добавьте текст ответа или приложите файл перед отправкой");
      return;
    }

    try {
      await onSubmit({ answerMarkdown: answer, files });
      setAnswer("");
      setFiles([]);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
      message.success("Ответ отправлен");
    } catch (error) {
      message.error(error?.response?.data?.detail || "Не удалось отправить ответ");
    }
  }

  async function handleUpdate() {
    if (!currentSubmission) return;
    if (!answer.trim() && files.length === 0 && !(currentSubmission.attachments || []).length) {
      message.warning("Добавьте текст ответа или приложите файл перед сохранением");
      return;
    }

    try {
      await onUpdate(currentSubmission, { answerMarkdown: answer, files });
      setFiles([]);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
      setIsEditing(false);
      message.success("Ответ обновлен");
    } catch (error) {
      message.error(error?.response?.data?.detail || "Не удалось обновить ответ");
    }
  }

  async function handleDelete() {
    if (!currentSubmission) return;
    try {
      await onDelete(currentSubmission);
      setAnswer("");
      setFiles([]);
      setIsEditing(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
      message.success("Ответ удален");
    } catch (error) {
      message.error(error?.response?.data?.detail || "Не удалось удалить ответ");
    }
  }

  const hasDraftContent = Boolean(answer.trim() || files.length || (currentSubmission?.attachments || []).length);

  return (
    <Card className="assignment-card">
      <div className="assignment-card-head">
        <div>
          <Space wrap>
            <Typography.Title level={4} className="assignment-title">
              {assignment.title}
            </Typography.Title>
            {assignment.max_score != null ? <Tag color="gold">До {assignment.max_score} баллов</Tag> : null}
            {currentSubmission ? (
              <Tag color={currentSubmission.status === "graded" ? "green" : "blue"}>
                {currentSubmission.status === "graded" ? "Проверено" : "Попытка отправлена"}
              </Tag>
            ) : null}
          </Space>
          <Typography.Text type="secondary">
            {currentSubmission
              ? "У вас уже есть сохраненный ответ. Его можно изменить или удалить."
              : "Отправьте один актуальный ответ. После отправки он сохранится как текущее решение."}
          </Typography.Text>
        </div>
      </div>

      <div className="assignment-markdown-card">
        <MarkdownContent value={assignment.instructions_markdown} />
      </div>

      {(assignment.attachments || []).length ? (
        <div className="assignment-attachment-row">
          <Typography.Text strong>Материалы к заданию:</Typography.Text>
          <AttachmentList attachments={assignment.attachments} />
        </div>
      ) : null}

      {!currentSubmission || isEditing ? (
        <div className="assignment-submit-block">
          <Typography.Title level={5}>{currentSubmission ? "Редактирование ответа" : "Ваш ответ"}</Typography.Title>
          <MarkdownEditor
            value={answer}
            onChange={setAnswer}
            placeholder="Опишите решение, приложите аргументы, выводы или краткий разбор."
            rows={8}
            minHeight={220}
          />

          <div className="assignment-file-picker">
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.zip,.rar,.7z,.pptx,.doc,.docx,.txt"
              multiple
              hidden
              onChange={(event) => handlePickFiles(event.target.files)}
            />
            <div className="assignment-file-picker-actions">
              <Typography.Text type="secondary">
                Можно приложить несколько файлов: PDF, архивы, презентации или документы.
              </Typography.Text>
              <Button onClick={() => fileInputRef.current?.click()}>
                {currentSubmission ? "Заменить файлы" : "Выбрать файлы"}
              </Button>
            </div>

            {(currentSubmission?.attachments || []).length && files.length === 0 ? (
              <AttachmentList attachments={currentSubmission.attachments} emptyText="Файлы не приложены" />
            ) : null}

            {files.length ? (
              <div className="attachment-list">
                {files.map((file) => (
                  <Typography.Text key={`${file.name}-${file.size}`} strong>
                    Новый файл: {file.name}
                  </Typography.Text>
                ))}
              </div>
            ) : null}
          </div>

          {!hasDraftContent ? (
            <Alert
              type="info"
              showIcon
              message="Добавьте текст ответа или выберите файл"
              description="Можно отправить только текст, только файл или оба варианта сразу."
            />
          ) : null}

          <Space wrap>
            <Button
              type="primary"
              loading={currentSubmission ? submissionUpdating : submissionPending}
              disabled={!hasDraftContent}
              onClick={currentSubmission ? handleUpdate : handleCreate}
            >
              {currentSubmission ? "Сохранить изменения" : "Отправить ответ"}
            </Button>
            {currentSubmission ? (
              <Button
                onClick={() => {
                  setIsEditing(false);
                  resetDraft();
                }}
              >
                Отменить
              </Button>
            ) : null}
          </Space>
        </div>
      ) : (
        <div className="assignment-attempts-stack">
          <Space wrap className="assignment-submission-actions">
            <Button onClick={() => setIsEditing(true)}>Редактировать ответ</Button>
            <Popconfirm
              title="Удалить ответ?"
              description="После удаления можно будет отправить новый ответ с нуля."
              okText="Удалить"
              cancelText="Отмена"
              onConfirm={handleDelete}
            >
              <Button danger loading={submissionDeleting}>
                Удалить ответ
              </Button>
            </Popconfirm>
          </Space>

          <Typography.Title level={5}>Состояние ответа</Typography.Title>
          <Descriptions bordered column={1} size="middle" className="assignment-status-table">
            <Descriptions.Item label="Состояние ответа на задание">
              {currentSubmission.status === "graded" ? "Ответ проверен преподавателем" : "Отправлено для оценивания"}
            </Descriptions.Item>
            <Descriptions.Item label="Состояние оценивания">
              {currentSubmission.status === "graded" ? (
                <span className="assignment-status-value assignment-status-value-success">Оценено</span>
              ) : (
                <span className="assignment-status-value">Ожидает проверки</span>
              )}
            </Descriptions.Item>
            <Descriptions.Item label="Последнее изменение">{formatDate(currentSubmission.updated_at)}</Descriptions.Item>
            <Descriptions.Item label="Ответ в виде файла">
              <AttachmentList attachments={currentSubmission.attachments || []} emptyText="Файлы не приложены" />
            </Descriptions.Item>
            <Descriptions.Item label="Текст ответа">
              {currentSubmission.answer_markdown ? (
                <div className="assignment-markdown-card compact">
                  <MarkdownContent value={currentSubmission.answer_markdown} />
                </div>
              ) : (
                <Typography.Text type="secondary">Текстовый ответ не добавлен</Typography.Text>
              )}
            </Descriptions.Item>
            <Descriptions.Item label="Оценка">
              {currentSubmission.score != null ? (
                <Tag color="gold">{currentSubmission.score}</Tag>
              ) : (
                <Typography.Text type="secondary">Пока не выставлена</Typography.Text>
              )}
            </Descriptions.Item>
          </Descriptions>

          {currentSubmission.feedback_markdown ? (
            <>
              <Alert type="info" showIcon message="Комментарий преподавателя" className="assignment-feedback-alert" />
              <div className="assignment-markdown-card compact">
                <MarkdownContent value={currentSubmission.feedback_markdown} />
              </div>
            </>
          ) : null}
        </div>
      )}
    </Card>
  );
}
