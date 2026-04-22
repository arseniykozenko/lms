import React from "react";
import { HolderOutlined, RightOutlined } from "@ant-design/icons";
import { Button, Card, Space, Tag, Typography } from "antd";
import { Link } from "react-router-dom";

export function CourseModuleCard({
  module,
  canManageCourse,
  reorderingModules,
  draggedModuleId,
  onDragStart,
  onDragOver,
  onDrop,
  onDragEnd,
  onEdit,
}) {
  return (
    <Card
      className={`module-card ${draggedModuleId === module.id ? "module-card-dragging" : ""}`}
      draggable={canManageCourse && !reorderingModules}
      onDragStart={() => onDragStart(module.id)}
      onDragOver={onDragOver}
      onDrop={() => onDrop(module.id)}
      onDragEnd={onDragEnd}
    >
      <div className="module-card-head">
        <div className="module-card-head-main">
          <Typography.Text type="secondary">Модуль {module.position}</Typography.Text>
          <Typography.Title level={4} className="module-card-title">
            {module.title}
          </Typography.Title>
        </div>
        <Space wrap>
          {canManageCourse ? (
            <Tag icon={<HolderOutlined />} color="default">
              Перетащить
            </Tag>
          ) : null}
          <Tag color={module.is_published ? "green" : "orange"}>
            {module.is_published ? "Опубликован" : "Черновик"}
          </Tag>
          {canManageCourse ? <Button onClick={() => onEdit(module)}>Редактировать</Button> : null}
        </Space>
      </div>

      <Typography.Paragraph className="module-card-description">
        {module.description || "Описание модуля пока не добавлено."}
      </Typography.Paragraph>

      <div className="module-card-footer">
        <Typography.Text type="secondary">
          Контент модуля открывается на отдельной странице: текст, видео, PDF и встроенные материалы.
        </Typography.Text>
        <Button type="primary">
          <Link to={`/modules/${module.id}`}>
            Открыть модуль <RightOutlined />
          </Link>
        </Button>
      </div>
    </Card>
  );
}
