import React from "react";
import { RobotOutlined, UserOutlined } from "@ant-design/icons";
import { AutoComplete, Avatar, Button, Card, Col, Form, Input, List, Modal, Row, Skeleton, Space, Tag, Typography, message } from "antd";
import { useUnit } from "effector-react";
import { useNavigate, useParams } from "react-router-dom";

import {
  getCourseCollaborators,
  inviteCourseCollaborator,
  removeCourseCollaborator,
  searchTeachers,
} from "../api/courses";
import { AppShell } from "../components/AppShell";
import { CourseHeroCard } from "../components/courses/CourseHeroCard";
import { CourseModuleDrawer } from "../components/courses/CourseModuleDrawer";
import { CourseModulesSection } from "../components/courses/CourseModulesSection";
import { CourseStudentsModal } from "../components/courses/CourseStudentsModal";
import { PageBreadcrumbs } from "../components/shared/PageBreadcrumbs";
import { getErrorMessage } from "../lib/errors";
import { getUserDisplayName } from "../lib/userName";
import { $courses, $user } from "../models/auth";
import {
  $courseEnrollPending,
  $studentAiInsightsByCourseId,
  $studentAiInsightsErrorByCourseId,
  $studentAiInsightsPending,
  $courseStudentRemovePending,
  $courseStudents,
  $courseStudentsPending,
  $moduleCreatePending,
  $moduleReorderPending,
  $moduleUpdatePending,
  $selectedCourse,
  $selectedCourseModules,
  $selectedCourseModulesPending,
  $selectedCoursePending,
  courseModulesReordered,
  coursePageOpened,
  coursePageReset,
  createModuleFx,
  enrollCourseFx,
  loadStudentCourseAiInsightsFx,
  loadCourseModulesFx,
  loadCourseStudentsFx,
  removeCourseStudentFx,
  updateModuleFx,
} from "../models/courses";

const defaultModuleValues = {
  title: "",
  description: "",
  is_published: false,
};

function reorderModulesList(modules, draggedId, targetId) {
  const next = [...modules];
  const fromIndex = next.findIndex((item) => item.id === draggedId);
  const toIndex = next.findIndex((item) => item.id === targetId);

  if (fromIndex === -1 || toIndex === -1 || fromIndex === toIndex) {
    return modules;
  }

  const [moved] = next.splice(fromIndex, 1);
  next.splice(toIndex, 0, moved);
  return next;
}

function roleLabel(role) {
  if (role === "admin") return "Администратор";
  return "Преподаватель";
}

export function CourseDetailsPage() {
  const { courseId } = useParams();
  const navigate = useNavigate();
  const [
    user,
    myCourses,
    course,
    modules,
    courseStudents,
    coursePending,
    modulesPending,
    courseStudentsPending,
    enrolling,
    studentAiPending,
    studentAiByCourseId,
    studentAiErrorByCourseId,
    removingStudent,
    creatingModule,
    updatingModule,
    reorderingModules,
    openCoursePage,
    resetCoursePage,
    submitEnroll,
    loadStudentAiInsights,
    loadCourseStudents,
    reloadModules,
    submitCreateModule,
    submitUpdateModule,
    submitReorderModules,
    submitRemoveStudent,
  ] = useUnit([
    $user,
    $courses,
    $selectedCourse,
    $selectedCourseModules,
    $courseStudents,
    $selectedCoursePending,
    $selectedCourseModulesPending,
    $courseStudentsPending,
    $courseEnrollPending,
    $studentAiInsightsPending,
    $studentAiInsightsByCourseId,
    $studentAiInsightsErrorByCourseId,
    $courseStudentRemovePending,
    $moduleCreatePending,
    $moduleUpdatePending,
    $moduleReorderPending,
    coursePageOpened,
    coursePageReset,
    enrollCourseFx,
    loadStudentCourseAiInsightsFx,
    loadCourseStudentsFx,
    loadCourseModulesFx,
    createModuleFx,
    updateModuleFx,
    courseModulesReordered,
    removeCourseStudentFx,
  ]);

  const [modulesLocked, setModulesLocked] = React.useState(false);
  const [moduleDrawerOpen, setModuleDrawerOpen] = React.useState(false);
  const [studentsOpen, setStudentsOpen] = React.useState(false);
  const [editingModule, setEditingModule] = React.useState(null);
  const [draggedModuleId, setDraggedModuleId] = React.useState(null);
  const [form] = Form.useForm();
  const [inviteForm] = Form.useForm();
  const [collaborators, setCollaborators] = React.useState([]);
  const [collaboratorsPending, setCollaboratorsPending] = React.useState(false);
  const [invitePending, setInvitePending] = React.useState(false);
  const [collaboratorsModalOpen, setCollaboratorsModalOpen] = React.useState(false);
  const [isCollaborator, setIsCollaborator] = React.useState(false);
  const [teacherOptions, setTeacherOptions] = React.useState([]);
  const [teacherSearchPending, setTeacherSearchPending] = React.useState(false);
  const [removeCollaboratorPendingId, setRemoveCollaboratorPendingId] = React.useState(null);
  const [hasModuleAccess, setHasModuleAccess] = React.useState(null);
  const [enrollModalOpen, setEnrollModalOpen] = React.useState(false);
  const teacherSearchTimerRef = React.useRef(null);
  const teacherSearchSeqRef = React.useRef(0);

  React.useEffect(() => {
    if (!courseId) return undefined;
    setModulesLocked(false);
    setHasModuleAccess(null);
    openCoursePage(courseId);
    return () => resetCoursePage();
  }, [courseId, openCoursePage, resetCoursePage]);

  React.useEffect(() => {
    if (!courseId) return;
    reloadModules(courseId).catch((error) => {
      if (error?.response?.status === 403) {
        setModulesLocked(true);
        setHasModuleAccess(false);
        return;
      }
      message.error(getErrorMessage(error, "Не удалось загрузить модули курса"));
    });
  }, [courseId, reloadModules]);

  React.useEffect(() => {
    if (modulesLocked) return;
    if (!modulesPending) {
      setHasModuleAccess(true);
    }
  }, [modulesLocked, modulesPending]);

  const isTeacher = user?.role === "teacher" || user?.role === "admin";
  const isOwnCourse = course?.author_id === user?.id;
  const canManageCourse = user?.role === "admin" || (isTeacher && (isOwnCourse || isCollaborator));
  const canInviteCollaborators = user?.role === "admin" || (isTeacher && isOwnCourse);
  const alreadyEnrolledFromStore = myCourses.some((item) => item.id === course?.id);
  const alreadyEnrolled = hasModuleAccess === null ? alreadyEnrolledFromStore : hasModuleAccess;
  const canEnrollCourse = !canManageCourse && (hasModuleAccess === false || (hasModuleAccess === null && !alreadyEnrolledFromStore));
  const savingModule = creatingModule || updatingModule;
  const canMessageTeacher = !canManageCourse && alreadyEnrolled && Boolean(course?.author_id);
  const roleContextTag = canManageCourse
    ? { color: "gold", label: "Режим: преподаватель" }
    : isTeacher && alreadyEnrolled
      ? { color: "blue", label: "Режим: слушатель (преподаватель)" }
      : isTeacher
        ? { color: "default", label: "Режим: гость (преподаватель)" }
        : alreadyEnrolled
          ? { color: "blue", label: "Режим: слушатель" }
          : { color: "default", label: "Режим: гость" };
  const roleContextHint = !canManageCourse && isTeacher
    ? "Вы можете проходить чужие курсы как слушатель. Управление курсом доступно только автору, соавтору или администратору."
    : "";
  const publishedModuleCount = modules.filter((module) => module.is_published).length;
  const studentCount = courseStudents.length;
  const averageStudentProgress = studentCount
    ? Math.round(courseStudents.reduce((total, item) => total + (item.progress?.progress_percent || 0), 0) / studentCount)
    : 0;
  const completedStudentCount = courseStudents.filter((item) => (item.progress?.progress_percent || 0) === 100).length;

  React.useEffect(() => {
    if (!courseId || !canManageCourse) return;
    loadCourseStudents(courseId).catch(() => {});
  }, [courseId, canManageCourse, loadCourseStudents]);

  React.useEffect(() => {
    if (!courseId || !isTeacher) return;
    setCollaboratorsPending(true);
    getCourseCollaborators(courseId)
      .then((items) => {
        setCollaborators(items);
        setIsCollaborator(items.some((item) => item.user_id === user?.id && item.status === "accepted"));
      })
      .catch(() => {
        setCollaborators([]);
        setIsCollaborator(false);
      })
      .finally(() => setCollaboratorsPending(false));
  }, [courseId, isTeacher, user?.id]);

  function openCreateModuleDrawer() {
    setEditingModule(null);
    form.setFieldsValue(defaultModuleValues);
    setModuleDrawerOpen(true);
  }

  function openEditModuleDrawer(module) {
    setEditingModule(module);
    form.setFieldsValue({
      title: module.title,
      description: module.description,
      is_published: module.is_published,
    });
    setModuleDrawerOpen(true);
  }

  function closeModuleDrawer() {
    setModuleDrawerOpen(false);
    setEditingModule(null);
    form.resetFields();
  }

  async function handleEnroll() {
    if (!courseId) return;
    setEnrollModalOpen(true);
  }

  async function confirmEnroll() {
    if (!courseId) return;
    try {
      await submitEnroll(courseId);
      setModulesLocked(false);
      setHasModuleAccess(true);
      setEnrollModalOpen(false);
      message.success("Вы записались на курс");

      try {
        await reloadModules(courseId);
      } catch (modulesError) {
        setModulesLocked(true);
        setHasModuleAccess(false);
        message.warning(getErrorMessage(modulesError, "Запись оформлена, но модули пока не открылись. Обновите страницу."));
      }
    } catch (error) {
      if (error?.response?.status === 403) {
        message.error(`Запись недоступна (403): ${error?.response?.data?.detail || "недостаточно прав"}`);
        return;
      }
      message.error(getErrorMessage(error, "Не удалось записаться на курс"));
    }
  }

  async function handleSaveModule(values) {
    if (!courseId) return;
    try {
      if (editingModule) {
        await submitUpdateModule({ moduleId: editingModule.id, payload: values });
        message.success("Модуль обновлен");
      } else {
        await submitCreateModule({ ...values, course_id: courseId });
        message.success("Модуль создан");
      }
      closeModuleDrawer();
      setModulesLocked(false);
    } catch (error) {
      message.error(getErrorMessage(error, "Не удалось сохранить модуль"));
    }
  }

  async function handleRemoveStudent(studentId) {
    if (!courseId || !studentId || studentId === "undefined") return;
    try {
      await submitRemoveStudent({ courseId, studentId });
      message.success("Студент удален с курса");
    } catch (error) {
      message.error(getErrorMessage(error, "Не удалось удалить студента с курса"));
    }
  }

  async function handleInviteCollaborator(values) {
    if (!courseId) return;
    if (!canInviteCollaborators) {
      message.warning("Только автор курса или администратор может отправлять приглашения.");
      return;
    }
    setInvitePending(true);
    try {
      const normalizedEmail = String(values.teacher_email || "").trim().toLowerCase();
      const lookup = await searchTeachers(normalizedEmail);
      const exactMatch = lookup.some((item) => String(item.email || "").trim().toLowerCase() === normalizedEmail);
      if (!exactMatch) {
        inviteForm.setFields([
          { name: "teacher_email", errors: ["Этот email не зарегистрирован как аккаунт преподавателя."] },
        ]);
        message.error("Этот email не зарегистрирован как аккаунт преподавателя.");
        return;
      }

      await inviteCourseCollaborator(courseId, {
        teacher_email: normalizedEmail,
        message: values.message || null,
      });
      const items = await getCourseCollaborators(courseId);
      setCollaborators(items);
      inviteForm.resetFields();
      setTeacherOptions([]);
      message.success("Приглашение отправлено");
    } catch (error) {
      if (error?.response?.status === 404) {
        inviteForm.setFields([
          { name: "teacher_email", errors: ["Этот email не зарегистрирован как аккаунт преподавателя."] },
        ]);
        message.error("Преподаватель с таким email не найден. Выберите преподавателя из подсказок.");
      } else if (error?.response?.status === 403) {
        message.error("Недостаточно прав для отправки приглашения.");
      } else {
        message.error(getErrorMessage(error, "Не удалось отправить приглашение"));
      }
    } finally {
      setInvitePending(false);
    }
  }

  async function handleRemoveCollaborator(collaboratorUserId) {
    if (!courseId) return;
    setRemoveCollaboratorPendingId(collaboratorUserId);
    try {
      await removeCourseCollaborator(courseId, collaboratorUserId);
      const items = await getCourseCollaborators(courseId);
      setCollaborators(items);
      message.success("Соавтор удален");
    } catch (error) {
      message.error(getErrorMessage(error, "Не удалось удалить соавтора"));
    } finally {
      setRemoveCollaboratorPendingId(null);
    }
  }

  function handleTeacherSearch(value) {
    const q = (value || "").trim();
    if (teacherSearchTimerRef.current) {
      clearTimeout(teacherSearchTimerRef.current);
    }
    if (!q) {
      setTeacherOptions([]);
      setTeacherSearchPending(false);
      return;
    }
    teacherSearchTimerRef.current = setTimeout(async () => {
      const seq = ++teacherSearchSeqRef.current;
      setTeacherSearchPending(true);
      try {
        const items = await searchTeachers(q);
        if (seq !== teacherSearchSeqRef.current) return;
        setTeacherOptions(
          items.map((item) => ({
            value: item.email,
            label: (
              <Space size={10} style={{ display: "flex", alignItems: "center" }}>
                <Avatar size="small" icon={<UserOutlined />} />
                <Space direction="vertical" size={0}>
                  <Typography.Text>{getUserDisplayName(item) || "Без имени"}</Typography.Text>
                  <Typography.Text type="secondary" style={{ fontSize: 12 }}>{item.email}</Typography.Text>
                </Space>
                <Tag color={item.role === "admin" ? "red" : "gold"}>{roleLabel(item.role)}</Tag>
              </Space>
            ),
          })),
        );
      } catch {
        if (seq !== teacherSearchSeqRef.current) return;
        setTeacherOptions([]);
      } finally {
        if (seq === teacherSearchSeqRef.current) {
          setTeacherSearchPending(false);
        }
      }
    }, 300);
  }

  React.useEffect(
    () => () => {
      if (teacherSearchTimerRef.current) {
        clearTimeout(teacherSearchTimerRef.current);
      }
    },
    [],
  );

  async function handleLoadStudentAi() {
    if (!courseId) return;
    await loadStudentAiInsights(courseId).catch((error) => {
      message.error(getErrorMessage(error, "Не удалось получить AI-рекомендации"));
    });
  }
  const studentAiInsights = courseId ? studentAiByCourseId[courseId] : null;
  const studentAiError = courseId ? studentAiErrorByCourseId[courseId] : "";

  function handleInviteFailed() {
    message.warning("Проверьте email преподавателя и попробуйте снова.");
  }

  function handleModuleDragOver(event) {
    if (canManageCourse) event.preventDefault();
  }

  async function handleDrop(targetModuleId) {
    if (!courseId || !draggedModuleId || draggedModuleId === targetModuleId) {
      setDraggedModuleId(null);
      return;
    }

    const reorderedModules = reorderModulesList(modules, draggedModuleId, targetModuleId);
    try {
      await submitReorderModules({ courseId, modules: reorderedModules });
      message.success("Порядок модулей обновлен");
    } catch (error) {
      message.error(getErrorMessage(error, "Не удалось изменить порядок модулей"));
    } finally {
      setDraggedModuleId(null);
    }
  }

  if (coursePending && !course) {
    return (
      <AppShell title="Курс" subtitle="Загружаем информацию о курсе.">
        <Card className="panel-card">
          <Skeleton active paragraph={{ rows: 8 }} />
        </Card>
      </AppShell>
    );
  }

  if (!course && !coursePending) {
    return (
      <AppShell title="Курс не найден" subtitle="Похоже, курс недоступен или был удален.">
        <Card className="panel-card">
          <Space direction="vertical" size="middle">
            <Typography.Paragraph className="panel-copy">
              Не удалось найти этот курс. Возможно, у вас нет доступа или ссылка устарела.
            </Typography.Paragraph>
            <Button type="primary" onClick={() => navigate("/courses")}>Вернуться в каталог</Button>
          </Space>
        </Card>
      </AppShell>
    );
  }

  return (
    <AppShell
      title={course?.title || "Курс"}
      subtitle={
        canManageCourse
          ? "Управляйте структурой курса, публикуйте модули и отслеживайте прогресс студентов."
          : "Изучайте описание курса и переходите к модулям, когда доступ уже открыт."
      }
    >
      <PageBreadcrumbs
        items={[
          { label: "Главная", href: "/dashboard" },
          { label: "Каталог курсов", href: "/courses" },
          { label: course?.title || "Курс" },
        ]}
      />

      <Row gutter={[20, 20]}>
        <Col xs={24} xl={canManageCourse ? 24 : 8}>
          <Space direction="vertical" size={20} style={{ width: "100%" }}>
            <CourseHeroCard
              course={course}
              canManageCourse={canManageCourse}
              alreadyEnrolled={alreadyEnrolled}
              canEnrollCourse={canEnrollCourse}
              roleContextTag={roleContextTag}
              roleContextHint={roleContextHint}
              enrolling={enrolling}
              moduleCount={modules.length}
              publishedModuleCount={publishedModuleCount}
              studentCount={studentCount}
              averageStudentProgress={averageStudentProgress}
              completedStudentCount={completedStudentCount}
              progressPageHref={course?.id ? `/courses/${course.id}/progress` : null}
              onEnroll={handleEnroll}
              onCreateModule={openCreateModuleDrawer}
              onOpenStudents={() => setStudentsOpen(true)}
            />

            {canManageCourse ? (
              <Card>
                <Space direction="vertical" size={12} style={{ width: "100%" }}>
                  <Space align="center" style={{ justifyContent: "space-between", width: "100%" }}>
                    <Typography.Title level={5} style={{ margin: 0 }}>Соавторы курса</Typography.Title>
                    <Button onClick={() => setCollaboratorsModalOpen(true)}>Управление</Button>
                  </Space>
                  <Typography.Text type="secondary">
                    Добавляйте преподавателей в соавторы. Соавтор может редактировать курс, но не удалять материалы автора.
                  </Typography.Text>
                  <Space wrap>
                    {collaborators
                      .filter((item) => item.status === "accepted")
                      .slice(0, 4)
                      .map((item) => (
                        <Tag key={item.id} color="gold">{item.user_name || item.user_email}</Tag>
                      ))}
                    {collaboratorsPending ? <Tag>Загрузка...</Tag> : null}
                  </Space>
                </Space>
              </Card>
            ) : null}

            {canMessageTeacher ? (
              <Card>
                <Space direction="vertical" size={12} style={{ width: "100%" }}>
                  <Typography.Title level={5} style={{ margin: 0 }}>Вопрос по курсу</Typography.Title>
                  <Typography.Text type="secondary">
                    Можно открыть личный чат и написать преподавателю напрямую.
                  </Typography.Text>
                  <Button type="default" onClick={() => navigate("/chat", { state: { partnerId: course.author_id } })}>
                    Открыть чат
                  </Button>
                </Space>
              </Card>
            ) : null}

            {!canManageCourse && alreadyEnrolled ? (
              <Card
                title="AI-ассистент обучения"
                extra={
                  <Button type="primary" icon={<RobotOutlined />} loading={studentAiPending} onClick={handleLoadStudentAi}>
                    Сгенерировать рекомендации
                  </Button>
                }
              >
                {studentAiError ? <Typography.Text type="danger">{studentAiError}</Typography.Text> : null}
                {studentAiInsights ? (
                  <Space direction="vertical" size={10} style={{ width: "100%" }}>
                    <Typography.Text strong>{studentAiInsights.summary}</Typography.Text>
                    <Space wrap>
                      <Tag color={studentAiInsights.risk_level === "high" ? "red" : studentAiInsights.risk_level === "medium" ? "orange" : "green"}>
                        Риск: {studentAiInsights.risk_level} ({studentAiInsights.risk_score}/100)
                      </Tag>
                      <Tag color="blue">Прогноз 7д: {studentAiInsights.predicted_progress_7d}%</Tag>
                      <Tag color="geekblue">14д: {studentAiInsights.predicted_progress_14d}%</Tag>
                      <Tag color="purple">30д: {studentAiInsights.predicted_progress_30d}%</Tag>
                    </Space>
                    <Typography.Text type="secondary">{studentAiInsights.cohort_comparison}</Typography.Text>
                    <div>
                      <Typography.Text strong>Что получается хорошо</Typography.Text>
                      <List
                        size="small"
                        dataSource={studentAiInsights.strengths || []}
                        renderItem={(item) => <List.Item>{item}</List.Item>}
                      />
                    </div>
                    <div>
                      <Typography.Text strong>На чем сфокусироваться</Typography.Text>
                      <List
                        size="small"
                        dataSource={studentAiInsights.focus_zones || []}
                        renderItem={(item) => <List.Item>{item}</List.Item>}
                      />
                    </div>
                    <div>
                      <Typography.Text strong>Рекомендации</Typography.Text>
                      <List
                        size="small"
                        dataSource={studentAiInsights.recommended_actions || []}
                        renderItem={(item) => <List.Item>{item}</List.Item>}
                      />
                    </div>
                  </Space>
                ) : (
                  <Typography.Text type="secondary">Нажмите «Сгенерировать рекомендации», чтобы получить персональный прогноз и план действий.</Typography.Text>
                )}
              </Card>
            ) : null}
          </Space>
        </Col>

        <Col xs={24} xl={canManageCourse ? 24 : 16}>
          <CourseModulesSection
            canManageCourse={canManageCourse}
            modulesLocked={modulesLocked}
            alreadyEnrolled={alreadyEnrolled}
            canEnrollCourse={canEnrollCourse}
            enrolling={enrolling}
            modules={modules}
            modulesPending={modulesPending}
            reorderingModules={reorderingModules}
            draggedModuleId={draggedModuleId}
            onEnroll={handleEnroll}
            onCreateModule={openCreateModuleDrawer}
            onDragStart={setDraggedModuleId}
            onDragOver={handleModuleDragOver}
            onDrop={handleDrop}
            onDragEnd={() => setDraggedModuleId(null)}
            onEdit={openEditModuleDrawer}
          />
        </Col>
      </Row>

      <CourseModuleDrawer
        open={moduleDrawerOpen}
        editingModule={editingModule}
        form={form}
        defaultModuleValues={defaultModuleValues}
        savingModule={savingModule}
        onClose={closeModuleDrawer}
        onSubmit={handleSaveModule}
      />

      <CourseStudentsModal
        open={studentsOpen}
        selectedCourse={course}
        courseStudents={courseStudents}
        courseStudentsPending={courseStudentsPending}
        removingStudent={removingStudent}
        onClose={() => setStudentsOpen(false)}
        onRemoveStudent={handleRemoveStudent}
      />

      <Modal
        title="Записаться на курс?"
        open={enrollModalOpen}
        onCancel={() => setEnrollModalOpen(false)}
        onOk={confirmEnroll}
        okText="Да, записаться"
        cancelText="Отмена"
        confirmLoading={enrolling}
      >
        <Typography.Paragraph style={{ marginBottom: 0 }}>
          После записи курс появится в разделе «Мои курсы», а также откроется доступ к модулям, AI-рекомендациям и чату с преподавателем.
        </Typography.Paragraph>
      </Modal>

      <Modal
        title="Соавторы курса"
        open={collaboratorsModalOpen}
        onCancel={() => {
          setCollaboratorsModalOpen(false);
          inviteForm.resetFields();
        }}
        footer={null}
        width={760}
        destroyOnClose
      >
        <Space direction="vertical" size={20} style={{ width: "100%" }}>
          <Card size="small">
            <Form form={inviteForm} layout="vertical" onFinish={handleInviteCollaborator} onFinishFailed={handleInviteFailed}>
              <Row gutter={12}>
                <Col xs={24} md={12}>
                  <Form.Item
                    label="Email преподавателя"
                    name="teacher_email"
                    rules={[
                      { required: true, message: "Укажите email преподавателя" },
                      { type: "email", message: "Введите корректный email" },
                    ]}
                  >
                    <AutoComplete options={teacherOptions} onSearch={handleTeacherSearch} filterOption={false}>
                      <Input placeholder="Начните вводить email или имя преподавателя" />
                    </AutoComplete>
                  </Form.Item>
                  <div style={{ minHeight: 20 }}>
                    {teacherSearchPending ? <Typography.Text type="secondary">Поиск преподавателей...</Typography.Text> : null}
                  </div>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item label="Сообщение (необязательно)" name="message">
                    <Input placeholder="Короткий комментарий к приглашению" />
                  </Form.Item>
                </Col>
              </Row>
              <Button htmlType="submit" type="primary" loading={invitePending}>
                Отправить приглашение
              </Button>
            </Form>
          </Card>

          <List
            bordered
            loading={collaboratorsPending}
            dataSource={collaborators}
            locale={{ emptyText: "Пока нет соавторов и приглашений" }}
            renderItem={(item) => (
              <List.Item
                actions={
                  canInviteCollaborators && item.user_id !== course?.author_id
                    ? [
                        <Button
                          key="remove-collaborator"
                          danger
                          size="small"
                          loading={removeCollaboratorPendingId === item.user_id}
                          onClick={() => handleRemoveCollaborator(item.user_id)}
                        >
                          Удалить
                        </Button>,
                      ]
                    : []
                }
              >
                <Space direction="vertical" size={2}>
                  <Typography.Text strong>{item.user_name || item.user_email}</Typography.Text>
                  <Typography.Text type="secondary">{item.user_email}</Typography.Text>
                  <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                    Пригласил: {item.inviter_name || item.inviter_email}
                  </Typography.Text>
                </Space>
                <Tag color={item.status === "accepted" ? "green" : item.status === "pending" ? "orange" : "default"}>
                  {item.status === "accepted" ? "Принято" : item.status === "pending" ? "Ожидает ответ" : "Отклонено"}
                </Tag>
              </List.Item>
            )}
          />
        </Space>
      </Modal>
    </AppShell>
  );
}
