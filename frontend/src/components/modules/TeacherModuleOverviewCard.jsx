import React from "react";
import {
  CheckSquareOutlined,
  FileTextOutlined,
  MessageOutlined,
  PlusOutlined,
  ReadOutlined,
} from "@ant-design/icons";
import { Button, Card, Space, Statistic, Tag, Typography } from "antd";
import { Link } from "react-router-dom";

export function TeacherModuleOverviewCard({
  module,
  contentCount,
  assignmentCount,
  hasQuiz,
  pendingSubmissionCount,
  onAddContent,
  onAddAssignment,
  onAddQuiz,
}) {
  return (
    <Card className="panel-card teacher-module-overview-card">
      <Space className="course-card-tags" wrap>
        <Tag color={module?.is_published ? "green" : "orange"}>
          {module?.is_published ? "Опубликован" : "Черновик"}
        </Tag>
        <Tag color="blue">Модуль {module?.position}</Tag>
        {pendingSubmissionCount > 0 ? <Tag color="gold">Ждут проверки: {pendingSubmissionCount}</Tag> : null}
      </Space>

      <div>
        <Typography.Title level={3} className="teacher-module-overview-title">
          {module?.title}
        </Typography.Title>
        <Typography.Paragraph className="panel-copy teacher-module-overview-copy">
          {module?.description || "Описание модуля пока не добавлено."}
        </Typography.Paragraph>
      </div>

      <div className="teacher-module-metrics">
        <div className="teacher-module-metric">
          <Statistic title="Материалы" value={contentCount} prefix={<ReadOutlined />} />
        </div>
        <div className="teacher-module-metric">
          <Statistic title="Задания" value={assignmentCount} prefix={<FileTextOutlined />} />
        </div>
        <div className="teacher-module-metric">
          <Statistic title="Тест" value={hasQuiz ? "Есть" : "Нет"} prefix={<CheckSquareOutlined />} />
        </div>
        <div className="teacher-module-metric">
          <Statistic title="На проверке" value={pendingSubmissionCount} prefix={<MessageOutlined />} />
        </div>
      </div>

      <Space wrap className="teacher-module-overview-actions">
        <Button>
          <Link to={`/courses/${module?.course_id}`}>Вернуться к курсу</Link>
        </Button>
        <Button type="primary" icon={<PlusOutlined />} onClick={onAddContent}>
          Добавить материал
        </Button>
        <Button onClick={onAddAssignment}>Добавить задание</Button>
        <Button onClick={onAddQuiz}>{hasQuiz ? "Редактировать тест" : "Создать тест"}</Button>
      </Space>

      <Typography.Text className="teacher-module-overview-note">
        {pendingSubmissionCount > 0
          ? "В модуле есть ответы студентов, которые ждут проверки. Их удобнее разбирать из секции заданий."
          : "Рабочая область ниже разбита по секциям, чтобы вам было удобнее управлять модулем по шагам."}
      </Typography.Text>
    </Card>
  );
}
