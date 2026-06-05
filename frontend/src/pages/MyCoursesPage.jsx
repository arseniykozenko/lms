import React from "react";
import { EyeInvisibleOutlined, UploadOutlined } from "@ant-design/icons";
import { Button, Card, Col, Empty, List, Row, Space, Tag, Typography, message } from "antd";
import { useUnit } from "effector-react";
import { Link } from "react-router-dom";

import { acceptCollaborationInvite, declineCollaborationInvite, getMyCollaborationInvites } from "../api/courses";
import { AppShell } from "../components/AppShell";
import { CourseCardItem } from "../components/courses/CourseCardItem";
import { getErrorMessage } from "../lib/errors";
import { $courses, $user } from "../models/auth";
import { $courseUpdatePending, updateCourseFx } from "../models/courses";

export function MyCoursesPage() {
  const [user, courses, updating, submitUpdate] = useUnit([$user, $courses, $courseUpdatePending, updateCourseFx]);
  const isTeacher = user?.role === "teacher" || user?.role === "admin";
  const [invites, setInvites] = React.useState([]);
  const [invitesPending, setInvitesPending] = React.useState(false);
  const [inviteActionPendingId, setInviteActionPendingId] = React.useState(null);

  async function loadInvites() {
    if (!isTeacher) return;
    setInvitesPending(true);
    try {
      const data = await getMyCollaborationInvites();
      setInvites(data);
    } catch (error) {
      message.error(getErrorMessage(error, "Не удалось загрузить приглашения в соавторы"));
    } finally {
      setInvitesPending(false);
    }
  }

  React.useEffect(() => {
    loadInvites();
  }, [isTeacher]);

  async function handlePublishToggle(course) {
    const nextPublished = !course.is_published;

    try {
      await submitUpdate({
        courseId: course.id,
        payload: { is_published: nextPublished },
      });
      message.success(nextPublished ? "Курс опубликован" : "Курс снят с публикации");
    } catch (error) {
      message.error(getErrorMessage(error, "Не удалось изменить статус курса"));
    }
  }

  async function handleInviteAction(inviteId, action) {
    setInviteActionPendingId(inviteId);
    try {
      if (action === "accept") {
        await acceptCollaborationInvite(inviteId);
        message.success("Приглашение принято");
      } else {
        await declineCollaborationInvite(inviteId);
        message.success("Приглашение отклонено");
      }
      await loadInvites();
    } catch (error) {
      message.error(getErrorMessage(error, "Не удалось обработать приглашение"));
    } finally {
      setInviteActionPendingId(null);
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
      {isTeacher ? (
        <Card className="panel-card" style={{ marginBottom: 20 }}>
          <Space direction="vertical" size={12} style={{ width: "100%" }}>
            <Typography.Title level={5} style={{ margin: 0 }}>
              Приглашения в соавторы
            </Typography.Title>
            <Typography.Text type="secondary">
              Здесь можно принять или отклонить приглашение на совместное ведение курса.
            </Typography.Text>
            <List
              bordered
              loading={invitesPending}
              dataSource={invites}
              locale={{ emptyText: "Новых приглашений нет" }}
              renderItem={(item) => (
                <List.Item
                  actions={[
                    <Button
                      key="accept"
                      type="primary"
                      size="small"
                      loading={inviteActionPendingId === item.id}
                      onClick={() => handleInviteAction(item.id, "accept")}
                    >
                      Принять
                    </Button>,
                    <Button
                      key="decline"
                      size="small"
                      danger
                      loading={inviteActionPendingId === item.id}
                      onClick={() => handleInviteAction(item.id, "decline")}
                    >
                      Отклонить
                    </Button>,
                  ]}
                >
                  <List.Item.Meta
                    title={item.course_title || "Курс"}
                    description={`Пригласил: ${item.inviter_name || item.inviter_email}${item.invite_message ? ` • ${item.invite_message}` : ""}`}
                  />
                </List.Item>
              )}
            />
          </Space>
        </Card>
      ) : null}

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
