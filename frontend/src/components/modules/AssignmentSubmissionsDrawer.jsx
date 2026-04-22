import React from "react";
import { Alert, Button, Collapse, Drawer, Empty, Form, Input, InputNumber, Segmented, Space, Tag, Typography } from "antd";

import { AttachmentList } from "../shared/AttachmentList";
import { MarkdownContent } from "../shared/MarkdownContent";
import { MarkdownEditor } from "../shared/MarkdownEditor";
import { formatDate } from "./moduleHelpers";

const FILTER_OPTIONS = [
  { label: "Все", value: "all" },
  { label: "На проверке", value: "pending" },
  { label: "Проверено", value: "graded" },
];

export function AssignmentSubmissionsDrawer({
  open,
  assignment,
  submissions,
  gradingPending,
  onClose,
  onGrade,
}) {
  const [filter, setFilter] = React.useState("all");
  const [search, setSearch] = React.useState("");

  const sortedSubmissions = React.useMemo(() => {
    return [...submissions].sort((left, right) => {
      const leftWeight = left.status === "graded" ? 1 : 0;
      const rightWeight = right.status === "graded" ? 1 : 0;
      if (leftWeight !== rightWeight) return leftWeight - rightWeight;
      return new Date(right.submitted_at).getTime() - new Date(left.submitted_at).getTime();
    });
  }, [submissions]);

  const visibleSubmissions = React.useMemo(() => {
    if (filter === "pending") {
      return sortedSubmissions.filter((submission) => submission.status !== "graded");
    }
    if (filter === "graded") {
      return sortedSubmissions.filter((submission) => submission.status === "graded");
    }
    return sortedSubmissions;
  }, [filter, sortedSubmissions]);

  const filteredSubmissions = React.useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return visibleSubmissions;

    return visibleSubmissions.filter((submission) => {
      const fullName = submission.student?.full_name?.toLowerCase() || "";
      const email = submission.student?.email?.toLowerCase() || "";
      return fullName.includes(query) || email.includes(query);
    });
  }, [search, visibleSubmissions]);

  if (!assignment) {
    return null;
  }

  return (
    <Drawer title={`Ответы на задание: ${assignment.title}`} width={760} open={open} onClose={onClose} destroyOnClose>
      {submissions.length === 0 ? (
        <Empty description="Пока никто не отправил ответ на это задание." />
      ) : (
        <div className="assignment-submission-filtered">
          <div className="assignment-submission-toolbar">
            <Typography.Text type="secondary">
              Неоцененные ответы показаны первыми, чтобы преподавателю было проще разбирать очередь.
            </Typography.Text>
            <Segmented options={FILTER_OPTIONS} value={filter} onChange={setFilter} />
          </div>

          <Input.Search
            allowClear
            placeholder="Найти по имени или email студента"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            className="assignment-submission-search"
          />

          {filteredSubmissions.length === 0 ? (
            <Empty description="Под выбранный фильтр пока нет ответов." />
          ) : (
            <Collapse
              accordion
              className="assignment-submission-collapse"
              items={filteredSubmissions.map((submission) => ({
                key: submission.id,
                label: <SubmissionSummary submission={submission} />,
                children: (
                  <AssignmentSubmissionPanel submission={submission} gradingPending={gradingPending} onGrade={onGrade} />
                ),
              }))}
            />
          )}
        </div>
      )}
    </Drawer>
  );
}

function SubmissionSummary({ submission }) {
  return (
    <div className="assignment-submission-summary">
      <div className="assignment-submission-summary-copy">
        <Typography.Title level={5} className="assignment-submission-summary-title">
          {submission.student?.full_name || submission.student?.email || "Студент"}
        </Typography.Title>
        <Typography.Text type="secondary">{formatDate(submission.submitted_at)}</Typography.Text>
      </div>

      <Space wrap>
        <Tag color={submission.status === "graded" ? "green" : "blue"}>
          {submission.status === "graded" ? "Проверено" : "На проверке"}
        </Tag>
        {submission.score != null ? <Tag color="gold">Оценка: {submission.score}</Tag> : null}
      </Space>
    </div>
  );
}

function AssignmentSubmissionPanel({ submission, gradingPending, onGrade }) {
  const [form] = Form.useForm();
  const [isEditing, setIsEditing] = React.useState(submission.status !== "graded");

  React.useEffect(() => {
    form.setFieldsValue({
      score: submission.score ?? undefined,
      feedback_markdown: submission.feedback_markdown || "",
    });
    setIsEditing(submission.status !== "graded");
  }, [form, submission]);

  async function handleFinish(values) {
    await onGrade(submission, values);
    setIsEditing(false);
  }

  return (
    <div className="assignment-submission-panel">
      {submission.answer_markdown ? (
        <div className="assignment-markdown-card">
          <Typography.Text type="secondary">Текст ответа</Typography.Text>
          <MarkdownContent value={submission.answer_markdown} />
        </div>
      ) : null}

      {(submission.attachments || []).length ? (
        <div className="assignment-attachment-row">
          <Typography.Text strong>Файлы ответа:</Typography.Text>
          <AttachmentList attachments={submission.attachments} />
        </div>
      ) : null}

      {!isEditing && submission.status === "graded" ? (
        <div className="assignment-graded-state">
          <Alert
            type="success"
            showIcon
            message="Ответ проверен"
            description={`Оценка сохранена${submission.score != null ? `: ${submission.score}` : ""}. При необходимости можно вернуться к редактированию решения.`}
          />

          {submission.feedback_markdown ? (
            <div className="assignment-markdown-card compact">
              <Typography.Text type="secondary">Комментарий преподавателя</Typography.Text>
              <MarkdownContent value={submission.feedback_markdown} />
            </div>
          ) : null}

          <Button onClick={() => setIsEditing(true)}>Изменить решение</Button>
        </div>
      ) : (
        <Form form={form} layout="vertical" onFinish={handleFinish}>
          <div className="assignment-grading-grid">
            <Form.Item name="score" label="Оценка">
              <InputNumber
                min={0}
                max={100}
                precision={0}
                controls={false}
                parser={(value) => {
                  const digits = String(value ?? "").replace(/[^\d]/g, "");
                  return digits ? Math.min(Number(digits), 100) : undefined;
                }}
                style={{ width: "100%" }}
              />
            </Form.Item>
          </div>

          <Form.Item name="feedback_markdown" label="Комментарий преподавателя">
            <MarkdownEditor
              placeholder="Можно кратко описать сильные стороны ответа и что стоит улучшить."
              rows={6}
              minHeight={180}
            />
          </Form.Item>

          <Space wrap>
            <Button type="primary" htmlType="submit" loading={gradingPending}>
              {submission.status === "graded" ? "Сохранить изменения" : "Выставить оценку"}
            </Button>
            {submission.status === "graded" ? (
              <Button onClick={() => setIsEditing(false)}>Оставить как есть</Button>
            ) : null}
          </Space>
        </Form>
      )}
    </div>
  );
}
