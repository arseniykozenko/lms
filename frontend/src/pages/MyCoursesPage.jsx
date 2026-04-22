import React from "react";
import { EyeInvisibleOutlined, UploadOutlined } from "@ant-design/icons";
import { Button, Card, Col, Empty, Row, Space, Tag, Typography, message } from "antd";
import { useUnit } from "effector-react";
import { Link } from "react-router-dom";

import { AppShell } from "../components/AppShell";
import { CourseCardItem } from "../components/courses/CourseCardItem";
import { $courses, $user } from "../models/auth";
import { $courseUpdatePending, updateCourseFx } from "../models/courses";

export function MyCoursesPage() {
  const [user, courses, updating, submitUpdate] = useUnit([$user, $courses, $courseUpdatePending, updateCourseFx]);
  const isTeacher = user?.role === "teacher" || user?.role === "admin";

  async function handlePublishToggle(course) {
    const nextPublished = !course.is_published;

    try {
      await submitUpdate({
        courseId: course.id,
        payload: { is_published: nextPublished },
      });
      message.success(nextPublished ? "Курс опубликован" : "Курс снят с публикации");
    } catch (error) {
      message.error(error?.response?.data?.detail || "Не удалось изменить статус курса");
    }
  }

  return (
    <AppShell
      title="Мои курсы"
      subtitle={
        isTeacher
          ? "Здесь собраны ваши авторские курсы и их текущий статус."
          : "Здесь собраны курсы, на которые вы уже записались."
      }
    >
      {courses.length === 0 ? (
        <Card className="panel-card">
          <Empty
            description={
              isTeacher ? "Вы еще не создали ни одного курса" : "Вы еще не записались ни на один курс"
            }
          />
        </Card>
      ) : (
        <Row gutter={[20, 20]}>
          {courses.map((course) => (
            <Col xs={24} md={12} xl={8} key={course.id}>
              <CourseCardItem
                course={course}
                tags={
                  isTeacher ? (
                    <Tag color={course.is_published ? "green" : "orange"}>
                      {course.is_published ? "Опубликован" : "Черновик"}
                    </Tag>
                  ) : null
                }
                footer={
                  <>
                    <Typography.Text type="secondary">
                      {isTeacher ? "Курс доступен для управления" : "Курс уже добавлен в ваш учебный кабинет"}
                    </Typography.Text>
                    <Space wrap>
                      <Button>
                        <Link to={`/courses/${course.id}`}>Открыть курс</Link>
                      </Button>
                      {isTeacher ? (
                        <Button
                          type={course.is_published ? "default" : "primary"}
                          icon={course.is_published ? <EyeInvisibleOutlined /> : <UploadOutlined />}
                          loading={updating}
                          onClick={() => handlePublishToggle(course)}
                        >
                          {course.is_published ? "Снять с публикации" : "Опубликовать"}
                        </Button>
                      ) : null}
                    </Space>
                  </>
                }
              />
            </Col>
          ))}
        </Row>
      )}
    </AppShell>
  );
}
