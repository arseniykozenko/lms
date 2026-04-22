import React from "react";
import { Button, Card, Col, Form, Row, Skeleton, Space, Typography, message } from "antd";
import { useUnit } from "effector-react";
import { useNavigate, useParams } from "react-router-dom";

import { AppShell } from "../components/AppShell";
import { CourseHeroCard } from "../components/courses/CourseHeroCard";
import { CourseModuleDrawer } from "../components/courses/CourseModuleDrawer";
import { CourseModulesSection } from "../components/courses/CourseModulesSection";
import { PageBreadcrumbs } from "../components/shared/PageBreadcrumbs";
import { $courses, $user } from "../models/auth";
import {
  $courseEnrollPending,
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
  loadCourseModulesFx,
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

export function CourseDetailsPage() {
  const { courseId } = useParams();
  const navigate = useNavigate();
  const [
    user,
    myCourses,
    course,
    modules,
    coursePending,
    modulesPending,
    enrolling,
    creatingModule,
    updatingModule,
    reorderingModules,
    openCoursePage,
    resetCoursePage,
    submitEnroll,
    reloadModules,
    submitCreateModule,
    submitUpdateModule,
    submitReorderModules,
  ] = useUnit([
    $user,
    $courses,
    $selectedCourse,
    $selectedCourseModules,
    $selectedCoursePending,
    $selectedCourseModulesPending,
    $courseEnrollPending,
    $moduleCreatePending,
    $moduleUpdatePending,
    $moduleReorderPending,
    coursePageOpened,
    coursePageReset,
    enrollCourseFx,
    loadCourseModulesFx,
    createModuleFx,
    updateModuleFx,
    courseModulesReordered,
  ]);

  const [modulesLocked, setModulesLocked] = React.useState(false);
  const [moduleDrawerOpen, setModuleDrawerOpen] = React.useState(false);
  const [editingModule, setEditingModule] = React.useState(null);
  const [draggedModuleId, setDraggedModuleId] = React.useState(null);
  const [form] = Form.useForm();

  React.useEffect(() => {
    if (!courseId) return undefined;

    setModulesLocked(false);
    openCoursePage(courseId);

    return () => {
      resetCoursePage();
    };
  }, [courseId, openCoursePage, resetCoursePage]);

  React.useEffect(() => {
    if (!courseId) return;

    reloadModules(courseId).catch((error) => {
      if (error?.response?.status === 403) {
        setModulesLocked(true);
        return;
      }

      message.error(error?.response?.data?.detail || "Не удалось загрузить модули курса");
    });
  }, [courseId, reloadModules]);

  const isTeacher = user?.role === "teacher" || user?.role === "admin";
  const isOwnCourse = course?.author_id === user?.id;
  const canManageCourse = user?.role === "admin" || (isTeacher && isOwnCourse);
  const alreadyEnrolled = myCourses.some((item) => item.id === course?.id);
  const savingModule = creatingModule || updatingModule;
  const publishedModuleCount = modules.filter((module) => module.is_published).length;

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

    try {
      await submitEnroll(courseId);
      await reloadModules(courseId);
      setModulesLocked(false);
      message.success("Вы записались на курс");
    } catch (error) {
      message.error(error?.response?.data?.detail || "Не удалось записаться на курс");
    }
  }

  async function handleSaveModule(values) {
    if (!courseId) return;

    try {
      if (editingModule) {
        await submitUpdateModule({
          moduleId: editingModule.id,
          payload: values,
        });
        message.success("Модуль обновлен");
      } else {
        await submitCreateModule({
          ...values,
          course_id: courseId,
        });
        message.success("Модуль создан");
      }

      closeModuleDrawer();
      setModulesLocked(false);
    } catch (error) {
      message.error(error?.response?.data?.detail || "Не удалось сохранить модуль");
    }
  }

  function handleModuleDragOver(event) {
    if (canManageCourse) {
      event.preventDefault();
    }
  }

  async function handleDrop(targetModuleId) {
    if (!courseId || !draggedModuleId || draggedModuleId === targetModuleId) {
      setDraggedModuleId(null);
      return;
    }

    const reorderedModules = reorderModulesList(modules, draggedModuleId, targetModuleId);

    try {
      await submitReorderModules({
        courseId,
        modules: reorderedModules,
      });
      message.success("Порядок модулей обновлен");
    } catch (error) {
      message.error(error?.response?.data?.detail || "Не удалось изменить порядок модулей");
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
            <Button type="primary" onClick={() => navigate("/courses")}>
              Вернуться в каталог
            </Button>
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
          ? "Управляйте структурой курса, публикуйте модули и собирайте контент внутри отдельных страниц модулей."
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
          <CourseHeroCard
            course={course}
            canManageCourse={canManageCourse}
            alreadyEnrolled={alreadyEnrolled}
            enrolling={enrolling}
            moduleCount={modules.length}
            publishedModuleCount={publishedModuleCount}
            onEnroll={handleEnroll}
            onCreateModule={openCreateModuleDrawer}
          />
        </Col>

        <Col xs={24} xl={canManageCourse ? 24 : 16}>
          <CourseModulesSection
            canManageCourse={canManageCourse}
            modulesLocked={modulesLocked}
            alreadyEnrolled={alreadyEnrolled}
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
    </AppShell>
  );
}
