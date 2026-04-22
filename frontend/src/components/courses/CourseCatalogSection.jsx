import React from "react";
import { Card, Col, Empty, Row, Tag, Typography } from "antd";

import { CourseCardItem } from "./CourseCardItem";

export function CourseCatalogSection({
  courses,
  catalogPending,
  isTeacher,
  userId,
  myCourseIds,
  renderCourseActions,
}) {
  if (courses.length === 0 && !catalogPending) {
    return (
      <Card className="panel-card">
        <Empty description="Пока нет доступных курсов" />
      </Card>
    );
  }

  return (
    <Row gutter={[20, 20]}>
      {courses.map((course) => {
        const isOwnCourse = course.author_id === userId;
        const alreadyInMyCourses = myCourseIds.has(course.id);

        return (
          <Col xs={24} md={12} xl={8} key={course.id}>
            <CourseCardItem
              course={course}
              loading={catalogPending}
              tags={
                <>
                  {isTeacher ? (
                    <Tag color={course.is_published ? "green" : "orange"}>
                      {course.is_published ? "Опубликован" : "Черновик"}
                    </Tag>
                  ) : null}
                  {isOwnCourse ? <Tag color="gold">Ваш курс</Tag> : null}
                  {alreadyInMyCourses && !isOwnCourse ? <Tag color="cyan">Уже записаны</Tag> : null}
                </>
              }
              footer={
                <>
                  <Typography.Text type="secondary">
                    {isOwnCourse ? "Вы автор этого курса" : "Курс доступен для записи"}
                  </Typography.Text>
                  {renderCourseActions(course, isOwnCourse, alreadyInMyCourses)}
                </>
              }
            />
          </Col>
        );
      })}
    </Row>
  );
}
