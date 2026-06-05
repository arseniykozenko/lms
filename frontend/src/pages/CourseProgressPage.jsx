import React from "react";
import { ArrowLeftOutlined, BulbOutlined, DownloadOutlined, QuestionCircleOutlined, RobotOutlined } from "@ant-design/icons";
import {
  Button,
  Card,
  Col,
  Empty,
  Input,
  List,
  Progress,
  Row,
  Segmented,
  Skeleton,
  Space,
  Statistic,
  Table,
  Tag,
  Tooltip,
  Typography,
} from "antd";
import { useUnit } from "effector-react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { AnalyticsChart } from "../components/analytics/AnalyticsChart";
import { AppShell } from "../components/AppShell";
import { downloadCourseAnalyticsZip, downloadCourseStudentsCsv } from "../api/courses";
import { PageBreadcrumbs } from "../components/shared/PageBreadcrumbs";
import { getUserDisplayName } from "../lib/userName";
import { $user } from "../models/auth";
import {
  $courseAiInsightsByCourseId,
  $courseAiInsightsErrorByCourseId,
  $courseAiInsightsPending,
  $courseStudents,
  $courseStudentsPending,
  $selectedCourse,
  $selectedCoursePending,
  coursePageOpened,
  coursePageReset,
  loadCourseAiInsightsFx,
  loadCourseStudentsFx,
} from "../models/courses";
import { useThemeMode } from "../theme/ThemeProvider";

function getStudentDisplayName(enrollment) {
  return getUserDisplayName(enrollment.user);
}

function getStatusLabel(status) {
  if (status === "completed") return "Завершили";
  if (status === "in_progress") return "В процессе";
  return "Не начали";
}

function getStatusColor(status) {
  if (status === "completed") return "green";
  if (status === "in_progress") return "blue";
  return "default";
}

function getRiskLabel(level) {
  if (level === "high") return "Высокий";
  if (level === "medium") return "Средний";
  return "Низкий";
}

function getRiskColor(level) {
  if (level === "high") return "red";
  if (level === "medium") return "orange";
  return "green";
}

function formatDateTime(value) {
  if (!value) return "Нет активности";
  return new Date(value).toLocaleString("ru-RU");
}

function HelpTitle({ text, help, iconColor = "#64748b" }) {
  return (
    <Space size={6}>
      <span>{text}</span>
      <Tooltip title={help}>
        <QuestionCircleOutlined style={{ color: iconColor }} />
      </Tooltip>
    </Space>
  );
}

export function CourseProgressPage() {
  const { courseId } = useParams();
  const navigate = useNavigate();
  const [statusFilter, setStatusFilter] = React.useState("all");
  const [riskFilter, setRiskFilter] = React.useState("all");
  const [query, setQuery] = React.useState("");
  const { mode } = useThemeMode();
  const isDark = mode === "dark";

  const [user, course, coursePending, students, studentsPending, aiPending, aiByCourseId, aiErrorByCourseId, openCoursePage, resetCoursePage, loadStudents, loadAiInsights] = useUnit([
    $user,
    $selectedCourse,
    $selectedCoursePending,
    $courseStudents,
    $courseStudentsPending,
    $courseAiInsightsPending,
    $courseAiInsightsByCourseId,
    $courseAiInsightsErrorByCourseId,
    coursePageOpened,
    coursePageReset,
    loadCourseStudentsFx,
    loadCourseAiInsightsFx,
  ]);

  React.useEffect(() => {
    if (!courseId) return undefined;
    openCoursePage(courseId);
    loadStudents(courseId).catch(() => {});

    return () => {
      resetCoursePage();
    };
  }, [courseId, openCoursePage, resetCoursePage, loadStudents]);

  async function handleDownloadCsv() {
    if (!course?.id) return;
    const blob = await downloadCourseStudentsCsv(course.id);
    const url = window.URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `students_${course.title || "course"}.csv`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    window.URL.revokeObjectURL(url);
  }

  async function handleDownloadFullAnalytics() {
    if (!course?.id) return;
    const blob = await downloadCourseAnalyticsZip(course.id);
    const url = window.URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `analytics_${course.title || "course"}.zip`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    window.URL.revokeObjectURL(url);
  }

  async function handleGenerateAiInsights() {
    if (!course?.id) return;
    await loadAiInsights({ courseId: course.id, studentsLimit: 15 }).catch(() => {});
  }
  const aiInsights = course?.id ? aiByCourseId[course.id] : null;
  const aiError = course?.id ? aiErrorByCourseId[course.id] : "";
  const aiLoading = aiPending;

  const isTeacher = user?.role === "teacher" || user?.role === "admin";
  const canManageCourse = isTeacher && (user?.role === "admin" || course?.author_id === user?.id);

  const filteredStudents = students
    .filter((enrollment) => (statusFilter === "all" ? true : enrollment.progress_status === statusFilter))
    .filter((enrollment) => (riskFilter === "all" ? true : enrollment.risk_level === riskFilter))
    .filter((enrollment) => {
      const haystack = `${getStudentDisplayName(enrollment)} ${enrollment.user.email}`.toLowerCase();
      return haystack.includes(query.trim().toLowerCase());
    });

  const averageProgress = students.length
    ? Math.round(students.reduce((total, enrollment) => total + (enrollment.progress?.progress_percent || 0), 0) / students.length)
    : 0;
  const averageRiskScore = students.length
    ? Math.round(students.reduce((total, enrollment) => total + (enrollment.risk_score || 0), 0) / students.length)
    : 0;
  const totalActiveLastWeek = students.reduce((total, enrollment) => total + (enrollment.recent_activity_count_7d || 0), 0);
  const totalCompletedLastWeek = students.reduce((total, enrollment) => total + (enrollment.recent_completed_items_7d || 0), 0);
  const highRiskCount = students.filter((item) => item.risk_level === "high").length;
  const mediumRiskCount = students.filter((item) => item.risk_level === "medium").length;
  const lowProgressCount = students.filter(
    (item) => item.progress_status === "in_progress" && (item.progress?.progress_percent || 0) < 50,
  ).length;
  const overdueCount = students.filter((item) => (item.overdue_items_count || 0) > 0).length;
  const noActivity7dCount = students.filter((item) => (item.inactivity_days || 0) >= 7).length;
  const pseudoActivityCount = students.filter((item) => item.pseudo_activity).length;
  const pendingReviewCount = students.filter((item) => (item.pending_assignments_count || 0) > 0).length;
  const failedQuizCount = students.filter((item) => (item.failed_quizzes_count || 0) > 0).length;
  const deadlinePressureCount = students.filter((item) => (item.upcoming_deadlines_count || 0) > 0).length;
  const lateSubmissionsCount = students.filter((item) => (item.late_submissions_count || 0) > 0).length;
  const stalledCount = students.filter((item) => item.engagement_trend === "stalled").length;
  const avgQuizScoreItems = students.filter((item) => item.average_quiz_score_percent !== null);
  const avgAssignmentScoreItems = students.filter((item) => item.average_assignment_score_percent !== null);
  const averageQuizScore = avgQuizScoreItems.length
    ? Math.round(avgQuizScoreItems.reduce((total, item) => total + (item.average_quiz_score_percent || 0), 0) / avgQuizScoreItems.length)
    : 0;
  const averageAssignmentScore = avgAssignmentScoreItems.length
    ? Math.round(
        avgAssignmentScoreItems.reduce((total, item) => total + (item.average_assignment_score_percent || 0), 0) /
          avgAssignmentScoreItems.length,
      )
    : 0;
  const completionRate = students.length
    ? Math.round((students.filter((item) => item.progress_status === "completed").length / students.length) * 100)
    : 0;

  const moduleAnalytics = React.useMemo(() => {
    const map = new Map();
    students.forEach((enrollment) => {
      (enrollment.progress?.modules || []).forEach((module) => {
        const current = map.get(module.module_id) || {
          moduleId: module.module_id,
          moduleTitle: module.module_title,
          totalProgress: 0,
          studentCount: 0,
          completedCount: 0,
          startedCount: 0,
        };
        current.totalProgress += module.progress_percent || 0;
        current.studentCount += 1;
        if ((module.progress_percent || 0) > 0) current.startedCount += 1;
        if ((module.progress_percent || 0) === 100) current.completedCount += 1;
        map.set(module.module_id, current);
      });
    });
    return Array.from(map.values())
      .map((item) => ({
        ...item,
        averageProgress: item.studentCount ? Math.round(item.totalProgress / item.studentCount) : 0,
      }))
      .sort((left, right) => left.averageProgress - right.averageProgress);
  }, [students]);

  const weakestModule = moduleAnalytics[0] || null;

  const statusChartData = React.useMemo(
    () => ({
      labels: ["Не начали", "В процессе", "Завершили"],
      datasets: [
        {
          data: [
            students.filter((item) => item.progress_status === "not_started").length,
            students.filter((item) => item.progress_status === "in_progress").length,
            students.filter((item) => item.progress_status === "completed").length,
          ],
          backgroundColor: ["#cbd5e1", "#38bdf8", "#22c55e"],
          borderWidth: 0,
        },
      ],
    }),
    [students],
  );

  const riskChartData = React.useMemo(
    () => ({
      labels: ["Низкий", "Средний", "Высокий"],
      datasets: [
        {
          data: [
            students.filter((item) => item.risk_level === "low").length,
            students.filter((item) => item.risk_level === "medium").length,
            students.filter((item) => item.risk_level === "high").length,
          ],
          backgroundColor: ["#22c55e", "#f59e0b", "#ef4444"],
          borderWidth: 0,
        },
      ],
    }),
    [students],
  );

  const activityChartData = React.useMemo(
    () => ({
      labels: ["Активность за 7 дней", "Завершено за 7 дней"],
      datasets: [
        {
          label: "События",
          data: [
            students.reduce((total, enrollment) => total + (enrollment.recent_activity_count_7d || 0), 0),
            students.reduce((total, enrollment) => total + (enrollment.recent_completed_items_7d || 0), 0),
          ],
          backgroundColor: ["#06b6d4", "#10b981"],
          borderRadius: 12,
        },
      ],
    }),
    [students],
  );

  const participationLineData = React.useMemo(
    () => ({
      labels: students
        .slice()
        .sort((left, right) => (right.recent_activity_count_7d || 0) - (left.recent_activity_count_7d || 0))
        .slice(0, 8)
        .map((item) => getStudentDisplayName(item).split(" ")[0]),
      datasets: [
        {
          label: "Активность за 7 дней",
          data: students
            .slice()
            .sort((left, right) => (right.recent_activity_count_7d || 0) - (left.recent_activity_count_7d || 0))
            .slice(0, 8)
            .map((item) => item.recent_activity_count_7d || 0),
          borderColor: "#14b8a6",
          backgroundColor: "rgba(20, 184, 166, 0.18)",
          tension: 0.35,
          fill: true,
          pointRadius: 4,
          pointHoverRadius: 6,
        },
      ],
    }),
    [students],
  );

  const moduleChartData = React.useMemo(
    () => ({
      labels: moduleAnalytics.map((module) => module.moduleTitle),
      datasets: [
        {
          label: "Средний прогресс по модулю",
          data: moduleAnalytics.map((module) => module.averageProgress),
          backgroundColor: moduleAnalytics.map((module) =>
            module.moduleId === weakestModule?.moduleId ? "#fb7185" : "#22d3ee",
          ),
          borderRadius: 10,
        },
      ],
    }),
    [moduleAnalytics, weakestModule],
  );

  const axisTickColor = isDark ? "#e2e8f0" : "#475569";
  const axisGridColor = isDark ? "rgba(148,163,184,0.34)" : "rgba(148,163,184,0.2)";
  const legendColor = isDark ? "#e2e8f0" : "#475569";
  const helpIconColor = isDark ? "#cdd8e8" : "#64748b";

  const barOptions = React.useMemo(
    () => ({
      plugins: { legend: { display: false } },
      scales: {
        y: {
          beginAtZero: true,
          ticks: { color: axisTickColor, precision: 0, stepSize: 1 },
          grid: { color: axisGridColor },
        },
        x: {
          ticks: { color: axisTickColor },
          grid: { display: false },
        },
      },
    }),
    [axisGridColor, axisTickColor],
  );

  const doughnutOptions = React.useMemo(
    () => ({
      plugins: {
        legend: {
          position: "bottom",
          labels: {
            color: legendColor,
          },
        },
      },
    }),
    [legendColor],
  );

  const lineOptions = React.useMemo(
    () => ({
      plugins: {
        legend: { display: false },
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: { color: axisTickColor, precision: 0, stepSize: 1 },
          grid: { color: axisGridColor },
        },
        x: {
          ticks: { color: axisTickColor },
          grid: { display: false },
        },
      },
    }),
    [axisGridColor, axisTickColor],
  );

  const columns = [
    {
      title: "Студент",
      key: "student",
      sorter: (a, b) => getStudentDisplayName(a).localeCompare(getStudentDisplayName(b), "ru"),
      render: (_, enrollment) => (
        <Space direction="vertical" size={0}>
          <Typography.Text strong>{getStudentDisplayName(enrollment)}</Typography.Text>
          <Typography.Text type="secondary">{enrollment.user.email}</Typography.Text>
        </Space>
      ),
    },
    {
      title: "Статус",
      dataIndex: "progress_status",
      key: "status",
      render: (status) => <Tag color={getStatusColor(status)}>{getStatusLabel(status)}</Tag>,
    },
    {
      title: "Риск",
      key: "risk",
      render: (_, enrollment) => (
        <Tag color={getRiskColor(enrollment.risk_level)}>
          {getRiskLabel(enrollment.risk_level)}: {enrollment.risk_score || 0}/100
        </Tag>
      ),
    },
    {
      title: "Прогресс",
      key: "progress",
      sorter: (a, b) => (a.progress?.progress_percent || 0) - (b.progress?.progress_percent || 0),
      render: (_, enrollment) => (
        <Space direction="vertical" size={4} style={{ width: 220 }}>
          <Progress percent={enrollment.progress?.progress_percent || 0} size="small" status="active" />
          <Typography.Text type="secondary">
            {enrollment.progress?.completed_items || 0} из {enrollment.progress?.total_items || 0}
          </Typography.Text>
        </Space>
      ),
    },
    {
      title: "Последняя активность",
      key: "last_activity_at",
      render: (_, enrollment) => <Typography.Text type="secondary">{formatDateTime(enrollment.last_activity_at)}</Typography.Text>,
    },
  ];

  if ((coursePending && !course) || (!course && studentsPending)) {
    return (
      <AppShell title="Аналитика курса" subtitle="Загружаем данные по прогрессу студентов.">
        <Card className="panel-card">
          <Skeleton active paragraph={{ rows: 10 }} />
        </Card>
      </AppShell>
    );
  }

  if (!course) {
    return (
      <AppShell title="Курс не найден" subtitle="Не удалось открыть страницу аналитики.">
        <Card className="panel-card">
          <Button type="primary" onClick={() => navigate("/courses")}>Вернуться в каталог</Button>
        </Card>
      </AppShell>
    );
  }

  if (!canManageCourse) {
    return (
      <AppShell title="Доступ ограничен" subtitle="Страница доступна преподавателю курса и администратору.">
        <Card className="panel-card">
          <Button type="primary"><Link to={`/courses/${course.id}`}>Вернуться к курсу</Link></Button>
        </Card>
      </AppShell>
    );
  }

  return (
    <AppShell
      title={`Аналитика курса: ${course.title}`}
      subtitle="Прогресс студентов, риски, активность и выгрузка полной отчетности."
    >
      <PageBreadcrumbs
        items={[
          { label: "Главная", href: "/dashboard" },
          { label: "Каталог курсов", href: "/courses" },
          { label: course.title, href: `/courses/${course.id}` },
          { label: "Аналитика" },
        ]}
      />

      <Space style={{ marginBottom: 20 }}>
        <Button icon={<ArrowLeftOutlined />}>
          <Link to={`/courses/${course.id}`}>Назад к курсу</Link>
        </Button>
      </Space>

      <Row gutter={[20, 20]}>
        <Col xs={24} md={12} xl={6}>
          <Card className="analytics-kpi analytics-kpi--students">
            <Statistic title={<HelpTitle iconColor={helpIconColor} text="Студентов" help="Количество студентов, записанных на курс." />} value={students.length} />
          </Card>
        </Col>
        <Col xs={24} md={12} xl={6}>
          <Card className="analytics-kpi analytics-kpi--progress">
            <Statistic title={<HelpTitle iconColor={helpIconColor} text="Средний прогресс" help="Средний процент прогресса по всем студентам курса." />} value={`${averageProgress}%`} />
          </Card>
        </Col>
        <Col xs={24} md={12} xl={6}>
          <Card className="analytics-kpi analytics-kpi--risk">
            <Statistic title={<HelpTitle iconColor={helpIconColor} text="Средний риск (балл)" help="Средняя оценка риска от 0 до 100 с учетом дедлайнов, активности и результатов." />} value={`${averageRiskScore}/100`} />
          </Card>
        </Col>
        <Col xs={24} md={12} xl={6}>
          <Card className="analytics-kpi analytics-kpi--velocity">
            <Statistic title={<HelpTitle iconColor={helpIconColor} text="Высокий риск (студенты)" help="Количество студентов с уровнем риска high." />} value={highRiskCount} />
          </Card>
        </Col>
        <Col xs={24} md={12} xl={6}>
          <Card className="analytics-kpi analytics-kpi--students">
            <Statistic title="Средний балл тестов" value={avgQuizScoreItems.length ? `${averageQuizScore}%` : "—"} />
          </Card>
        </Col>
        <Col xs={24} md={12} xl={6}>
          <Card className="analytics-kpi analytics-kpi--progress">
            <Statistic title="Средний балл заданий" value={avgAssignmentScoreItems.length ? `${averageAssignmentScore}%` : "—"} />
          </Card>
        </Col>

        <Col xs={24} lg={16}>
          <Card size="small" title={<HelpTitle iconColor={helpIconColor} text="Участие студентов" help="Активность каждого студента за 7 дней: просмотры контента, задания, квизы." />}>
            <AnalyticsChart type="line" data={participationLineData} options={lineOptions} height={300} />
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card size="small" title={<HelpTitle iconColor={helpIconColor} text="Завершение и риск" help="Распределение студентов по статусу прогресса и уровням риска." />}>
            <Space direction="vertical" style={{ width: "100%" }} size={18}>
              <AnalyticsChart type="doughnut" data={statusChartData} options={doughnutOptions} height={180} />
              <AnalyticsChart type="doughnut" data={riskChartData} options={doughnutOptions} height={180} />
              <Typography.Text type="secondary">Доля завершивших курс: {completionRate}%</Typography.Text>
            </Space>
          </Card>
        </Col>
        <Col xs={24}>
          <Card size="small" title={<HelpTitle iconColor={helpIconColor} text="Активность за неделю" help="Общее число событий активности и завершенных учебных действий за 7 дней." />}>
            <AnalyticsChart type="bar" data={activityChartData} options={barOptions} height={220} />
          </Card>
        </Col>

        <Col xs={24}>
          <Card className="panel-card" title={<HelpTitle iconColor={helpIconColor} text="Аналитические сигналы" help="Набор индикаторов для быстрого выявления проблемных зон в обучении." />}>
            <Row gutter={[12, 12]}>
              <Col xs={24} md={12} xl={8}>
                <Card size="small">
                  <Statistic title="Средний риск (студенты)" value={mediumRiskCount} />
                </Card>
              </Col>
              <Col xs={24} md={12} xl={8}>
                <Card size="small">
                  <Statistic title="Низкий прогресс (< 50%)" value={lowProgressCount} />
                </Card>
              </Col>
              <Col xs={24} md={12} xl={8}>
                <Card size="small">
                  <Statistic title="Есть просрочки" value={overdueCount} />
                </Card>
              </Col>
              <Col xs={24} md={12} xl={8}>
                <Card size="small">
                  <Statistic title="Нет активности 7 дней" value={noActivity7dCount} />
                </Card>
              </Col>
              <Col xs={24} md={12} xl={8}>
                <Card size="small">
                  <Statistic title={<HelpTitle iconColor={helpIconColor} text="Псевдоактивность" help="Есть активность в просмотрах материалов, но нет заметного учебного продвижения." />} value={pseudoActivityCount} />
                </Card>
              </Col>
              <Col xs={24} md={12} xl={8}>
                <Card size="small">
                  <Statistic title="На проверке у преподавателя" value={pendingReviewCount} />
                </Card>
              </Col>
              <Col xs={24} md={12} xl={8}>
                <Card size="small">
                  <Statistic title="Темп (завершено/активность)" value={`${totalCompletedLastWeek}/${totalActiveLastWeek}`} />
                </Card>
              </Col>
              <Col xs={24} md={12} xl={8}>
                <Card size="small">
                  <Statistic title="Проблемы с тестами" value={failedQuizCount} />
                </Card>
              </Col>
              <Col xs={24} md={12} xl={8}>
                <Card size="small">
                  <Statistic title="Ближайшие дедлайны" value={deadlinePressureCount} />
                </Card>
              </Col>
              <Col xs={24} md={12} xl={8}>
                <Card size="small">
                  <Statistic title="Поздние сдачи" value={lateSubmissionsCount} />
                </Card>
              </Col>
              <Col xs={24} md={12} xl={8}>
                <Card size="small">
                  <Statistic title={<HelpTitle iconColor={helpIconColor} text="Стагнация активности" help="Студенты без значимого прогресса: долгий простой или псевдоактивность." />} value={stalledCount} />
                </Card>
              </Col>
            </Row>
          </Card>
        </Col>

        <Col xs={24}>
          <Card className="panel-card" title="Прогресс по модулям">
            {moduleAnalytics.length === 0 ? (
              <Empty description="Недостаточно данных по модулям для расчета аналитики" />
            ) : (
              <Space direction="vertical" style={{ width: "100%" }} size={16}>
                <AnalyticsChart type="bar" data={moduleChartData} options={barOptions} height={280} />
                {weakestModule ? (
                  <Typography.Text type="secondary">
                    Модуль с минимальным средним прогрессом: {weakestModule.moduleTitle} ({weakestModule.averageProgress}%).
                  </Typography.Text>
                ) : null}
                <Row gutter={[12, 12]}>
                  {moduleAnalytics.map((module) => (
                    <Col xs={24} md={12} xl={8} key={module.moduleId}>
                      <Card size="small">
                        <Space direction="vertical" style={{ width: "100%" }} size={8}>
                          <Typography.Text strong>{module.moduleTitle}</Typography.Text>
                          <Progress percent={module.averageProgress} size="small" status="active" />
                          <Typography.Text type="secondary">
                            Начали: {module.startedCount}/{module.studentCount}
                          </Typography.Text>
                          <Typography.Text type="secondary">
                            Завершили: {module.completedCount}/{module.studentCount}
                          </Typography.Text>
                        </Space>
                      </Card>
                    </Col>
                  ))}
                </Row>
              </Space>
            )}
          </Card>
        </Col>

        <Col xs={24}>
          <Card
            className="panel-card"
            title="AI-прогноз и рекомендации"
            extra={
              <Button type="primary" icon={<RobotOutlined />} loading={aiLoading} onClick={handleGenerateAiInsights}>
                Сгенерировать прогноз и рекомендации
              </Button>
            }
          >
            {aiError ? <Typography.Text type="danger">{aiError}</Typography.Text> : null}
            {!aiInsights && !aiLoading ? (
              <Empty description="Нажмите «Сгенерировать прогноз и рекомендации», чтобы получить прогнозы и рекомендации от AI." />
            ) : null}
            {aiInsights ? (
              <Space direction="vertical" size={14} style={{ width: "100%" }}>
                <Card size="small">
                  <Space direction="vertical" size={8} style={{ width: "100%" }}>
                    <Typography.Text strong>{aiInsights.course_forecast?.summary}</Typography.Text>
                    <Space wrap>
                      <Tag color="blue">Завершение 7д: {aiInsights.course_forecast?.completion_forecast_7d}%</Tag>
                      <Tag color="geekblue">Завершение 14д: {aiInsights.course_forecast?.completion_forecast_14d}%</Tag>
                      <Tag color="purple">Завершение 30д: {aiInsights.course_forecast?.completion_forecast_30d}%</Tag>
                      <Tag color="orange">Средний прогресс 14д: {aiInsights.course_forecast?.average_progress_forecast_14d}%</Tag>
                      <Tag color="red">High-risk 14д: {aiInsights.course_forecast?.high_risk_share_forecast_14d}%</Tag>
                    </Space>
                  </Space>
                </Card>

                <Row gutter={[12, 12]}>
                  {(aiInsights.course_forecast?.key_actions || []).map((item, index) => (
                    <Col xs={24} md={12} xl={8} key={`${item.action}-${index}`}>
                      <Card size="small">
                        <Space direction="vertical" size={6}>
                          <Space>
                            <BulbOutlined />
                            <Tag color={item.priority === "P1" ? "red" : item.priority === "P2" ? "orange" : "blue"}>
                              {item.priority}
                            </Tag>
                            <Tag>{item.horizon_days} дн.</Tag>
                          </Space>
                          <Typography.Text strong>{item.action}</Typography.Text>
                          <Typography.Text type="secondary">{item.why}</Typography.Text>
                          <Typography.Text>{item.expected_effect}</Typography.Text>
                        </Space>
                      </Card>
                    </Col>
                  ))}
                </Row>

                {(aiInsights.early_risk_signals || []).length ? (
                  <Card size="small" title="Ранние сигналы риска">
                    <Row gutter={[12, 12]}>
                      {(aiInsights.early_risk_signals || []).map((signal, index) => (
                        <Col xs={24} md={12} xl={6} key={`${signal.label}-${index}`}>
                          <Card size="small">
                            <Space direction="vertical" size={6}>
                              <Typography.Text strong>{signal.label}</Typography.Text>
                              <Tag color={signal.severity === "high" ? "red" : signal.severity === "medium" ? "orange" : "green"}>
                                {signal.severity === "high" ? "Высокий приоритет" : signal.severity === "medium" ? "Средний приоритет" : "Низкий приоритет"}
                              </Tag>
                              <Typography.Text>{signal.value} (порог: {signal.threshold})</Typography.Text>
                              <Typography.Text type="secondary">{signal.note}</Typography.Text>
                            </Space>
                          </Card>
                        </Col>
                      ))}
                    </Row>
                  </Card>
                ) : null}

                {aiInsights.intervention_plan ? (
                  <Card size="small" title={`План вмешательства (${aiInsights.intervention_plan.horizon_days} дней)`}>
                    <Space direction="vertical" size={10} style={{ width: "100%" }}>
                      <Typography.Text strong>{aiInsights.intervention_plan.focus}</Typography.Text>
                      <List
                        size="small"
                        dataSource={(aiInsights.intervention_plan.tasks || []).slice(0, 8)}
                        renderItem={(task) => (
                          <List.Item>
                            <Space direction="vertical" size={2}>
                              <Space wrap>
                                <Typography.Text strong>{task.student_name}</Typography.Text>
                                <Tag color={task.risk === "high" ? "red" : task.risk === "medium" ? "orange" : "green"}>{task.risk}</Tag>
                                <Tag>{task.eta_days} дн.</Tag>
                              </Space>
                              <Typography.Text>{task.action}</Typography.Text>
                              <Typography.Text type="secondary">{task.success_metric}</Typography.Text>
                            </Space>
                          </List.Item>
                        )}
                      />
                      <Typography.Text type="secondary">{aiInsights.intervention_plan.expected_outcome}</Typography.Text>
                    </Space>
                  </Card>
                ) : null}

                <Typography.Text type="secondary">
                  Confidence: {aiInsights.meta?.confidence ?? "—"}%. Предпосылки: {(aiInsights.meta?.assumptions || []).join(" | ")}
                </Typography.Text>
              </Space>
            ) : null}
          </Card>
        </Col>

        <Col xs={24}>
          <Card className="panel-card">
            <Space wrap style={{ width: "100%", justifyContent: "space-between", marginBottom: 16 }}>
              <Space wrap>
                <Button icon={<DownloadOutlined />} onClick={handleDownloadCsv}>Скачать CSV по студентам</Button>
                <Button type="primary" icon={<DownloadOutlined />} onClick={handleDownloadFullAnalytics}>Скачать полную аналитику (ZIP)</Button>
              </Space>
              <Segmented
                value={statusFilter}
                onChange={setStatusFilter}
                options={[
                  { label: "Все", value: "all" },
                  { label: "Не начали", value: "not_started" },
                  { label: "В процессе", value: "in_progress" },
                  { label: "Завершили", value: "completed" },
                ]}
              />
              <Segmented
                value={riskFilter}
                onChange={setRiskFilter}
                options={[
                  { label: "Все риски", value: "all" },
                  { label: "Низкий", value: "low" },
                  { label: "Средний", value: "medium" },
                  { label: "Высокий", value: "high" },
                ]}
              />
              <Input.Search
                allowClear
                placeholder="Поиск по имени или email"
                style={{ width: 320 }}
                value={query}
                onChange={(event) => setQuery(event.target.value)}
              />
            </Space>

            {filteredStudents.length === 0 && !studentsPending ? (
              <Empty description="Нет студентов по выбранным фильтрам" />
            ) : (
              <Table
                rowKey={(record) => record.id}
                loading={studentsPending}
                dataSource={filteredStudents}
                columns={columns}
                pagination={{ pageSize: 10, hideOnSinglePage: true }}
                scroll={{ x: 1100 }}
              />
            )}
          </Card>
        </Col>
      </Row>
    </AppShell>
  );
}

