import React from "react";
import { BookOutlined, CheckCircleOutlined, EyeOutlined, PlusOutlined } from "@ant-design/icons";
import { Button, Card, Space, Statistic, Tag, Typography } from "antd";
import { Link } from "react-router-dom";

export function CourseHeroCard({
  course,
  canManageCourse,
  alreadyEnrolled,
  canEnrollCourse = false,
  roleContextTag = null,
  roleContextHint = "",
  enrolling,
  moduleCount,
  publishedModuleCount,
  studentCount = 0,
  averageStudentProgress = 0,
  completedStudentCount = 0,
  progressPageHref,
  onEnroll,
  onCreateModule,
  onOpenStudents,
}) {
  return (
    <Card
      className="panel-card course-hero-card"
      cover={
        <div
          className="course-card-cover course-hero-cover"
          style={
            course?.thumbnail_url
              ? {
                  backgroundImage: `linear-gradient(rgba(16,36,31,0.18), rgba(16,36,31,0.18)), url(${course.thumbnail_url})`,
                }
              : undefined
          }
        >
          {!course?.thumbnail_url ? <BookOutlined className="course-card-cover-icon" /> : null}
        </div>
      }
    >
      <Space className="course-card-tags" wrap>
        <Tag color={course?.is_published ? "green" : "orange"}>{course?.is_published ? "Опубликован" : "Черновик"}</Tag>
        {canManageCourse ? <Tag color="gold">Ваш курс</Tag> : null}
        {alreadyEnrolled && !canManageCourse ? <Tag color="cyan">Вы записаны</Tag> : null}
        {roleContextTag ? <Tag color={roleContextTag.color}>{roleContextTag.label}</Tag> : null}
      </Space>

      <Typography.Paragraph className="course-hero-description">
        {course?.description || "Описание курса пока не добавлено."}
      </Typography.Paragraph>

      {canManageCourse ? (
        <div className="course-hero-metrics">
          <div className="course-hero-metric">
            <Statistic title="Всего модулей" value={moduleCount} prefix={<BookOutlined />} />
          </div>
          <div className="course-hero-metric">
            <Statistic title="Опубликовано" value={publishedModuleCount} prefix={<EyeOutlined />} />
          </div>
          <div className="course-hero-metric">
            <Statistic title="Черновиков" value={Math.max(moduleCount - publishedModuleCount, 0)} prefix={<CheckCircleOutlined />} />
          </div>
          <div className="course-hero-metric">
            <Statistic title="Студентов" value={studentCount} prefix={<BookOutlined />} />
          </div>
          <div className="course-hero-metric">
            <Statistic title="Средний прогресс" value={`${averageStudentProgress}%`} prefix={<EyeOutlined />} />
          </div>
          <div className="course-hero-metric">
            <Statistic title="Завершили курс" value={completedStudentCount} prefix={<CheckCircleOutlined />} />
          </div>
        </div>
      ) : null}

      <Space wrap>
        <Button>
          <Link to="/courses">Назад в каталог</Link>
        </Button>
        {!canManageCourse && canEnrollCourse ? (
          <Button type="primary" loading={enrolling} onClick={onEnroll}>
            Записаться на курс
          </Button>
        ) : null}
        {canManageCourse ? (
          <>
            <Button type="primary" icon={<PlusOutlined />} onClick={onCreateModule}>
              Добавить модуль
            </Button>
            {progressPageHref ? (
              <Button>
                <Link to={progressPageHref}>Страница прогресса</Link>
              </Button>
            ) : null}
            <Button onClick={onOpenStudents}>Студенты и прогресс</Button>
          </>
        ) : null}
      </Space>

      {canManageCourse ? (
        <Typography.Text className="course-hero-note">
          Управляйте структурой курса сверху вниз: создавайте модули, публикуйте их и переходите внутрь для наполнения
          материалами, заданиями и тестами. В модалке студентов доступен прогресс каждого записанного студента.
        </Typography.Text>
      ) : null}
      {!canManageCourse && roleContextHint ? <Typography.Text type="secondary">{roleContextHint}</Typography.Text> : null}
    </Card>
  );
}
