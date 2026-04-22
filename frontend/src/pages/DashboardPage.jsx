import React from "react";
import { BookOutlined, ClockCircleOutlined, TeamOutlined } from "@ant-design/icons";
import { Button, Card, Col, List, Row, Statistic, Tag, Typography } from "antd";
import { useUnit } from "effector-react";
import { Link } from "react-router-dom";

import { AppShell } from "../components/AppShell";
import { $courses, $user } from "../models/auth";

export function DashboardPage() {
  const [user, courses] = useUnit([$user, $courses]);
  const isTeacher = user?.role === "teacher";

  const spotlight = isTeacher
    ? [
        "Опубликуйте структуру курса и план занятий",
        "Обновите профиль, чтобы повысить доверие студентов",
        "Подготовьте материалы модулей и квизов",
      ]
    : [
        "Заполните профиль и настройте учебное пространство",
        "Просматривайте опубликованные преподавателями курсы",
        "Следите за прогрессом и попытками прохождения квизов",
      ];

  return (
    <AppShell
      title={isTeacher ? "Кабинет преподавателя" : "Кабинет студента"}
      subtitle={
        isTeacher
          ? "Чистая панель управления для курсов, доверия и дальнейшего роста платформы."
          : "Ваше учебное пространство с профилем, доступом и активностью по курсам."
      }
    >
      <Row gutter={[20, 20]}>
        <Col xs={24} md={8}>
          <Card className="metric-card">
            <Statistic title="Роль" value={isTeacher ? "Преподаватель" : "Студент"} prefix={<TeamOutlined />} />
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card className="metric-card">
            <Statistic title="Курсов в доступе" value={courses.length} prefix={<BookOutlined />} />
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card className="metric-card">
            <Statistic
              title="Статус аккаунта"
              value={user?.is_active ? "Активен" : "Неактивен"}
              prefix={<ClockCircleOutlined />}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[20, 20]} className="dashboard-grid">
        <Col xs={24} lg={14}>
          <Card className="panel-card" title="Обзор роли">
            <Typography.Paragraph className="panel-copy">
              {isTeacher
                ? "Этот профиль оптимизирован для создания и управления учебным контентом. По мере появления курсов и модулей он легко расширится до полноценной панели преподавателя."
                : "Этот профиль оптимизирован для записи на курсы, прохождения учебного пути и отслеживания дальнейшей активности."}
            </Typography.Paragraph>
            <div className="tag-row">
              <Tag color="cyan">JWT подключен</Tag>
              <Tag color="geekblue">FastAPI backend</Tag>
              <Tag color={isTeacher ? "gold" : "green"}>{isTeacher ? "Режим преподавателя" : "Режим студента"}</Tag>
            </div>
          </Card>
        </Col>

        <Col xs={24} lg={10}>
          <Card className="panel-card" title="Следующие шаги">
            <List
              dataSource={spotlight}
              renderItem={(item) => (
                <List.Item>
                  <Typography.Text>{item}</Typography.Text>
                </List.Item>
              )}
            />
          </Card>
        </Col>

        <Col xs={24}>
          <Card
            className="panel-card"
            title="Мои курсы"
            extra={
              <Button type="link">
                <Link to={isTeacher ? "/courses" : "/my-courses"}>{isTeacher ? "Открыть каталог" : "Открыть все"}</Link>
              </Button>
            }
          >
            {courses.length === 0 ? (
              <Typography.Paragraph type="secondary">
                {isTeacher
                  ? "Вы еще не создали ни одного курса. Начните с каталога курсов и создайте первый курс."
                  : "Вы пока не записаны ни на один курс. После записи курсы появятся здесь."}
              </Typography.Paragraph>
            ) : (
              <List
                dataSource={courses}
                renderItem={(course) => (
                  <List.Item>
                    <List.Item.Meta title={course.title} description={course.description} />
                    {isTeacher ?<Tag color={course.is_published ? "green" : "orange"}>
                      {course.is_published ? "Опубликован" : "Черновик"}
                    </Tag>
                    :
                    null}
                  </List.Item>
                )}
              />
            )}
          </Card>
        </Col>
      </Row>
    </AppShell>
  );
}
