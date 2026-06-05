import React from "react";
import { Button, Card, Col, Empty, Row, Space, Typography } from "antd";

import { CourseModuleCard } from "./CourseModuleCard";

export function CourseModulesSection({
  canManageCourse,
  modulesLocked,
  alreadyEnrolled,
  canEnrollCourse = false,
  enrolling,
  modules,
  modulesPending,
  reorderingModules,
  draggedModuleId,
  onEnroll,
  onCreateModule,
  onDragStart,
  onDragOver,
  onDrop,
  onDragEnd,
  onEdit,
}) {
  return (
    <Card
      className="panel-card course-modules-panel"
      title="Модули курса"
      extra={
        canManageCourse ? (
          <Space wrap>
            <Typography.Text type="secondary">Перетаскивайте карточки, чтобы менять порядок модулей</Typography.Text>
            <Button type="link" onClick={onCreateModule}>
              Новый модуль
            </Button>
          </Space>
        ) : null
      }
    >
      <Typography.Paragraph className="panel-copy course-modules-copy">
        {canManageCourse
          ? "Здесь удобно следить за структурой курса: какие модули уже опубликованы, а какие еще остаются в черновиках."
          : "Откройте нужный модуль и переходите к материалам, заданию, тесту и обсуждению."}
      </Typography.Paragraph>

      {modulesLocked && !canManageCourse ? (
        <Empty description="Модули откроются после записи на курс" image={Empty.PRESENTED_IMAGE_SIMPLE}>
          {canEnrollCourse ? (
            <Button type="primary" loading={enrolling} onClick={onEnroll}>
              Записаться и открыть модули
            </Button>
          ) : null}
        </Empty>
      ) : modules.length === 0 && !modulesPending ? (
        <Empty
          description={
            canManageCourse ? "Модулей пока нет. Добавьте первый модуль курса." : "Пока нет опубликованных модулей"
          }
        />
      ) : (
        <Row gutter={[16, 16]}>
          {modules.map((module) => (
            <Col xs={24} key={module.id}>
              <CourseModuleCard
                module={module}
                canManageCourse={canManageCourse}
                reorderingModules={reorderingModules}
                draggedModuleId={draggedModuleId}
                onDragStart={onDragStart}
                onDragOver={onDragOver}
                onDrop={onDrop}
                onDragEnd={onDragEnd}
                onEdit={onEdit}
              />
            </Col>
          ))}
        </Row>
      )}
    </Card>
  );
}
