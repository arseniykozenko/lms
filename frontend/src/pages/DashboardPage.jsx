import React from "react";
import {
  BookOutlined,
  CalendarOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  ExclamationCircleOutlined,
  SafetyCertificateOutlined,
  TeamOutlined,
} from "@ant-design/icons";
import { Button, Card, Col, Empty, List, Progress, Row, Space, Statistic, Tag, Typography } from "antd";
import { useUnit } from "effector-react";
import { Link } from "react-router-dom";

import { AppShell } from "../components/AppShell";
import { isTeacherRole } from "../lib/roles";
import { $courses, $user } from "../models/auth";
import { $studentAiInsightsByCourseId, $studentAiInsightsPending, loadStudentCourseAiInsightsFx } from "../models/courses";

function getTrendLabel(value) {
  if (value === "growing") return "Рост";
  if (value === "stalled") return "Стагнация";
  return "Стабильно";
}

function getTrendColor(value) {
  if (value === "growing") return "green";
  if (value === "stalled") return "orange";
  return "blue";
}

function buildStudentQueue(courses) {
  return courses
    .map((course) => {
      const overdue = course.overdue_items_count || 0;
      const deadlines = course.upcoming_deadlines_count || 0;
      const pending = course.pending_assignments_count || 0;
      const progress = course.progress?.progress_percent || 0;
      const priority = overdue * 100 + deadlines * 50 + pending * 20 + (100 - progress);

      return {
        id: course.id,
        title: course.title,
        overdue,
        deadlines,
        pending,
        progress,
        priority,
      };
    })
    .sort((a, b) => b.priority - a.priority)
    .slice(0, 5);
}

function formatDateTime(value) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "-";
  return date.toLocaleString("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function DashboardPage() {
  const [user, courses, studentAiPending, studentAiByCourseId, loadStudentAiInsights] = useUnit([
    $user,
    $courses,
    $studentAiInsightsPending,
    $studentAiInsightsByCourseId,
    loadStudentCourseAiInsightsFx,
  ]);
  const isAdmin = user?.role === "admin";
  const isTeacher = isTeacherRole(user?.role);
  const isStudent = !isTeacher && !isAdmin;

  const averageProgress = courses.length
    ? Math.round(courses.reduce((sum, course) => sum + (course.progress?.progress_percent || 0), 0) / courses.length)
    : 0;

  const upcomingDeadlines = courses.reduce((sum, course) => sum + (course.upcoming_deadlines_count || 0), 0);
  const overdueItems = courses.reduce((sum, course) => sum + (course.overdue_items_count || 0), 0);
  const completedLastWeek = courses.reduce((sum, course) => sum + (course.recent_completed_items_7d || 0), 0);
  const pendingReviews = courses.reduce((sum, course) => sum + (course.pending_assignments_count || 0), 0);
  const queue = buildStudentQueue(courses);

  const authoredCourses = courses.filter((course) => course.author_id === user?.id);
  const collaboratedCourses = courses.filter((course) => course.author_id !== user?.id);
  const draftsCount = courses.filter((course) => !course.is_published).length;
  const publishedCount = courses.filter((course) => course.is_published).length;

  const lastActiveCourse = [...courses]
    .filter((course) => Boolean(course.last_activity_at))
    .sort((a, b) => new Date(b.last_activity_at).getTime() - new Date(a.last_activity_at).getTime())[0] || null;
  const studentAiInsights = lastActiveCourse?.id ? studentAiByCourseId[lastActiveCourse.id] : null;

  React.useEffect(() => {
    let active = true;
    async function run() {
      if (!isStudent || !lastActiveCourse?.id) {
        return;
      }
      try {
        if (!studentAiByCourseId[lastActiveCourse.id]) {
          await loadStudentAiInsights(lastActiveCourse.id);
        }
      } catch {
        if (!active) return;
      }
    }
    run();
    return () => {
      active = false;
    };
  }, [isStudent, lastActiveCourse?.id, loadStudentAiInsights, studentAiByCourseId]);

  const recentTeacherCourses = [...courses]
    .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())
    .slice(0, 5);
  const staleCoursesCount = courses.filter((course) => {
    const updatedAt = new Date(course.updated_at).getTime();
    if (Number.isNaN(updatedAt)) return false;
    return Date.now() - updatedAt > 1000 * 60 * 60 * 24 * 30;
  }).length;

  const title = isAdmin ? "Панель администратора" : isTeacher ? "Панель преподавателя" : "Мое обучение";
  const subtitle = isAdmin
    ? "Модерация, контроль контента и состояние платформы."
    : isTeacher
      ? "Управление курсами, публикацией и совместной работой."
      : "Прогресс, дедлайны и фокус на ближайшие шаги.";

  return (
    <AppShell title={title} subtitle={subtitle}>
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card className="metric-card">
            <Statistic title="Курсы" value={courses.length} prefix={<BookOutlined />} />
          </Card>
        </Col>

        {isStudent ? (
          <>
            <Col xs={24} sm={12} lg={6}>
              <Card className="metric-card">
                <Statistic title="Средний прогресс" value={`${averageProgress}%`} prefix={<CheckCircleOutlined />} />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card className="metric-card">
                <Statistic title="Дедлайны (7 дней)" value={upcomingDeadlines} prefix={<CalendarOutlined />} />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card className="metric-card">
                <Statistic title="Просрочки" value={overdueItems} prefix={<ExclamationCircleOutlined />} />
              </Card>
            </Col>
          </>
        ) : (
          <>
            <Col xs={24} sm={12} lg={6}>
              <Card className="metric-card">
                <Statistic title="Опубликовано" value={publishedCount} prefix={<CheckCircleOutlined />} />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card className="metric-card">
                <Statistic title="Черновики" value={draftsCount} prefix={<ClockCircleOutlined />} />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card className="metric-card">
                <Statistic title="На проверке" value={pendingReviews} prefix={<TeamOutlined />} />
              </Card>
            </Col>
          </>
        )}
      </Row>

      <Row gutter={[16, 16]} className="dashboard-grid">
        {isStudent ? (
          <>
            <Col xs={24} lg={9}>
              <Card className="panel-card" title="Приоритеты">
                {queue.length ? (
                  <List
                    dataSource={queue}
                    renderItem={(item) => (
                      <List.Item>
                        <Space direction="vertical" size={8} style={{ width: "100%" }}>
                          <Space wrap>
                            <Typography.Text strong>{item.title}</Typography.Text>
                            {item.overdue > 0 ? <Tag color="red">Просрочено: {item.overdue}</Tag> : null}
                            {item.deadlines > 0 ? <Tag color="gold">Дедлайны: {item.deadlines}</Tag> : null}
                            {item.pending > 0 ? <Tag color="blue">На проверке: {item.pending}</Tag> : null}
                          </Space>
                          <Progress percent={item.progress} size="small" status="active" />
                          <Button type="link" style={{ paddingInline: 0 }}>
                            <Link to={`/courses/${item.id}`}>Открыть курс</Link>
                          </Button>
                        </Space>
                      </List.Item>
                    )}
                  />
                ) : (
                  <Empty description="Пока нет данных для приоритетов" image={Empty.PRESENTED_IMAGE_SIMPLE} />
                )}
              </Card>
            </Col>

            <Col xs={24} lg={15}>
              <Card className="panel-card" title="Последняя активность">
                {lastActiveCourse ? (
                  <Space direction="vertical" size={10} style={{ width: "100%" }}>
                    <Typography.Title level={5} style={{ margin: 0 }}>
                      {lastActiveCourse.title}
                    </Typography.Title>
                    <Typography.Text type="secondary">
                      Последняя активность: {formatDateTime(lastActiveCourse.last_activity_at)}
                    </Typography.Text>
                    <Progress percent={lastActiveCourse.progress?.progress_percent || 0} size="small" status="active" />
                    <Space wrap>
                      <Tag color={getTrendColor(lastActiveCourse.engagement_trend)}>{getTrendLabel(lastActiveCourse.engagement_trend)}</Tag>
                      <Tag color="purple">Выполнено за 7 дней: {lastActiveCourse.recent_completed_items_7d || 0}</Tag>
                    </Space>
                    <Button type="primary">
                      <Link to={`/courses/${lastActiveCourse.id}`}>Продолжить курс</Link>
                    </Button>
                  </Space>
                ) : (
                  <Empty description="Активность по курсам еще не зафиксирована" image={Empty.PRESENTED_IMAGE_SIMPLE} />
                )}
              </Card>
            </Col>
            <Col xs={24}>
              <Card
                className="panel-card"
                title="AI-рекомендации по текущему курсу"
                extra={lastActiveCourse ? <Tag color="blue">{lastActiveCourse.title}</Tag> : null}
              >
                {studentAiPending ? (
                  <Typography.Text type="secondary">Формируем рекомендации...</Typography.Text>
                ) : studentAiInsights ? (
                  <Space direction="vertical" size={8} style={{ width: "100%" }}>
                    <Typography.Text strong>{studentAiInsights.summary}</Typography.Text>
                    <Space wrap>
                      <Tag color={studentAiInsights.risk_level === "high" ? "red" : studentAiInsights.risk_level === "medium" ? "orange" : "green"}>
                        Риск: {studentAiInsights.risk_level} ({studentAiInsights.risk_score}/100)
                      </Tag>
                      <Tag color="geekblue">Прогресс 14д: {studentAiInsights.predicted_progress_14d}%</Tag>
                    </Space>
                    <Typography.Text type="secondary">{studentAiInsights.cohort_comparison}</Typography.Text>
                    <List
                      size="small"
                      header={<Typography.Text strong>Ближайшие шаги</Typography.Text>}
                      dataSource={(studentAiInsights.recommended_actions || []).slice(0, 4)}
                      renderItem={(item) => <List.Item>{item}</List.Item>}
                    />
                  </Space>
                ) : (
                  <Empty description="Недостаточно данных для персональных рекомендаций" image={Empty.PRESENTED_IMAGE_SIMPLE} />
                )}
              </Card>
            </Col>
          </>
        ) : (
          <>
            <Col xs={24} lg={8}>
              <Card className="panel-card" title={isAdmin ? "Быстрые действия" : "Рабочие действия"}>
                <Space direction="vertical" size={10} style={{ width: "100%" }}>
                  <Button block icon={<BookOutlined />}>
                    <Link to="/courses">Открыть каталог курсов</Link>
                  </Button>
                  <Button block icon={<TeamOutlined />}>
                    <Link to="/my-courses">Открыть мои курсы</Link>
                  </Button>
                  {isAdmin ? (
                    <Button block icon={<SafetyCertificateOutlined />}>
                      <Link to="/moderation">Открыть модерацию</Link>
                    </Button>
                  ) : null}
                  <Button block icon={<CalendarOutlined />}>
                    <Link to="/chat">Открыть чат</Link>
                  </Button>
                </Space>
              </Card>
            </Col>

            <Col xs={24} lg={16}>
              <Card className="panel-card" title={isAdmin ? "Курсы под контролем" : "Нагрузка преподавателя"}>
                <Space size={[10, 10]} wrap>
                  <Tag color="blue">Автор: {authoredCourses.length}</Tag>
                  <Tag color="geekblue">Соавтор: {collaboratedCourses.length}</Tag>
                  <Tag color="green">Опубликовано: {publishedCount}</Tag>
                  <Tag color="orange">Черновики: {draftsCount}</Tag>
                </Space>
                <List
                  style={{ marginTop: 12 }}
                  dataSource={recentTeacherCourses}
                  locale={{ emptyText: "Курсы пока не добавлены" }}
                  renderItem={(course) => (
                    <List.Item
                      actions={[
                        <Tag key="status" color={course.is_published ? "green" : "orange"}>
                          {course.is_published ? "Опубликован" : "Черновик"}
                        </Tag>,
                      ]}
                    >
                      <List.Item.Meta
                        title={<Link to={`/courses/${course.id}`}>{course.title}</Link>}
                        description={`Обновлен: ${formatDateTime(course.updated_at)}`}
                      />
                    </List.Item>
                  )}
                />
              </Card>
            </Col>

            <Col xs={24}>
              <Card className="panel-card" title={isAdmin ? "Контроль и риски" : "Требует внимания сегодня"}>
                <Space size={[10, 10]} wrap>
                  <Tag color={draftsCount > 0 ? "orange" : "green"}>
                    {draftsCount > 0 ? `Черновики без публикации: ${draftsCount}` : "Нет зависших черновиков"}
                  </Tag>
                  <Tag color={staleCoursesCount > 0 ? "gold" : "green"}>
                    {staleCoursesCount > 0
                      ? `Давно не обновлялись (>30 дней): ${staleCoursesCount}`
                      : "Все курсы обновлялись недавно"}
                  </Tag>
                  <Tag color={collaboratedCourses.length > 0 ? "blue" : "default"}>
                    Соавторств: {collaboratedCourses.length}
                  </Tag>
                </Space>
              </Card>
            </Col>
          </>
        )}

        <Col xs={24}>
          <Card
            className="panel-card"
            title={isTeacher || isAdmin ? "Курсы под управлением" : "Мои курсы"}
            extra={
              <Button type="link">
                <Link to={isTeacher || isAdmin ? "/courses" : "/my-courses"}>Открыть все</Link>
              </Button>
            }
          >
            {courses.length === 0 ? (
              <Empty
                description={isTeacher || isAdmin ? "Добавьте первый курс в каталоге." : "Вы пока не записаны на курсы."}
                image={Empty.PRESENTED_IMAGE_SIMPLE}
              />
            ) : (
              <List
                dataSource={courses}
                renderItem={(course) => (
                  <List.Item
                    actions={
                      isTeacher || isAdmin
                        ? [
                            <Tag key="status" color={course.is_published ? "green" : "orange"}>
                              {course.is_published ? "Опубликован" : "Черновик"}
                            </Tag>,
                          ]
                        : [
                            <Button key="open" type="link">
                              <Link to={`/courses/${course.id}`}>Открыть</Link>
                            </Button>,
                          ]
                    }
                  >
                    <List.Item.Meta
                      title={course.title}
                      description={
                        isTeacher || isAdmin ? (
                          <Typography.Text type="secondary">{course.description}</Typography.Text>
                        ) : (
                          <Space direction="vertical" size={6} style={{ width: "100%" }}>
                            <Typography.Text type="secondary">{course.description}</Typography.Text>
                            <Progress percent={course.progress?.progress_percent || 0} size="small" status="active" />
                            <Space wrap size={[8, 8]}>
                              <Tag color={getTrendColor(course.engagement_trend)}>{getTrendLabel(course.engagement_trend)}</Tag>
                              {(course.recent_completed_items_7d || 0) > 0 ? (
                                <Tag color="green">Завершено за 7 дней: {course.recent_completed_items_7d}</Tag>
                              ) : null}
                            </Space>
                          </Space>
                        )
                      }
                    />
                  </List.Item>
                )}
              />
            )}
          </Card>
        </Col>

        {isStudent ? (
          <Col xs={24}>
            <Card className="panel-card" title="Динамика за 7 дней">
              <Space size={24} wrap>
                <Statistic title="Завершено" value={completedLastWeek} prefix={<CheckCircleOutlined />} />
                <Statistic title="Дедлайны" value={upcomingDeadlines} prefix={<CalendarOutlined />} />
                <Statistic title="Просрочки" value={overdueItems} prefix={<ClockCircleOutlined />} />
              </Space>
            </Card>
          </Col>
        ) : null}
      </Row>
    </AppShell>
  );
}
