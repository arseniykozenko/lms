import React from "react";
import {
  CloseCircleOutlined,
  DeleteOutlined,
  EditOutlined,
  EyeInvisibleOutlined,
  FilterOutlined,
  PlusOutlined,
  SearchOutlined,
  TeamOutlined,
  UploadOutlined,
} from "@ant-design/icons";
import { Badge, Button, Card, Form, Input, Modal, Popconfirm, Space, Tag, Typography, message } from "antd";
import { useUnit } from "effector-react";
import { Link } from "react-router-dom";

import { AppShell } from "../components/AppShell";
import { getCourseCategories } from "../api/courses";
import { CourseCatalogSection } from "../components/courses/CourseCatalogSection";
import { CourseEditorDrawer } from "../components/courses/CourseEditorDrawer";
import { CourseStudentsModal } from "../components/courses/CourseStudentsModal";
import { POPULAR_COURSE_CATEGORIES, normalizeCategory } from "../lib/courseCategories";
import { getErrorMessage } from "../lib/errors";
import { $courses, $user } from "../models/auth";
import {
  $catalogCourses,
  $catalogPending,
  $courseCreatePending,
  $courseDeletePending,
  $courseEnrollPending,
  $courseStudentRemovePending,
  $courseStudents,
  $courseStudentsPending,
  $courseThumbnailPending,
  $courseUpdatePending,
  createCourseFx,
  coursesPageOpened,
  deleteCourseFx,
  enrollCourseFx,
  loadCourseStudentsFx,
  loadCatalogCoursesFx,
  removeCourseStudentFx,
  updateCourseFx,
  uploadCourseThumbnailFx,
} from "../models/courses";

const defaultCourseValues = {
  title: "",
  description: "",
  category: "",
  is_published: false,
};

export function CoursesPage() {
  const [
    user,
    myCourses,
    catalogCourses,
    catalogPending,
    creating,
    enrolling,
    updating,
    uploadingThumbnail,
    deleting,
    courseStudents,
    courseStudentsPending,
    removingStudent,
    openPage,
    submitCreate,
    submitEnroll,
    submitUpdate,
    submitUploadThumbnail,
    submitDelete,
    fetchCourseStudents,
    submitRemoveStudent,
    loadCatalogCourses,
  ] = useUnit([
    $user,
    $courses,
    $catalogCourses,
    $catalogPending,
    $courseCreatePending,
    $courseEnrollPending,
    $courseUpdatePending,
    $courseThumbnailPending,
    $courseDeletePending,
    $courseStudents,
    $courseStudentsPending,
    $courseStudentRemovePending,
    coursesPageOpened,
    createCourseFx,
    enrollCourseFx,
    updateCourseFx,
    uploadCourseThumbnailFx,
    deleteCourseFx,
    loadCourseStudentsFx,
    loadCatalogCoursesFx,
    removeCourseStudentFx,
  ]);

  const [editorOpen, setEditorOpen] = React.useState(false);
  const [query, setQuery] = React.useState("");
  const [categoryFilters, setCategoryFilters] = React.useState([]);
  const [showAllCategories, setShowAllCategories] = React.useState(false);
  const [studentsOpen, setStudentsOpen] = React.useState(false);
  const [categories, setCategories] = React.useState([]);
  const [editingCourse, setEditingCourse] = React.useState(null);
  const [selectedCourse, setSelectedCourse] = React.useState(null);
  const [pendingPhoto, setPendingPhoto] = React.useState(null);
  const [previewUrl, setPreviewUrl] = React.useState("");
  const [photoHint, setPhotoHint] = React.useState("");
  const fileInputRef = React.useRef(null);
  const [form] = Form.useForm();

  React.useEffect(() => {
    openPage();
    // run once on mount; live updates are handled by explicit filter reloads below
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  React.useEffect(() => {
    getCourseCategories()
      .then(setCategories)
      .catch(() => setCategories([]));
  }, []);

  React.useEffect(() => {
    const timerId = window.setTimeout(() => {
      loadCatalogCourses({
        q: query.trim() || undefined,
      });
    }, 250);
    return () => window.clearTimeout(timerId);
  }, [query, loadCatalogCourses]);

  React.useEffect(() => {
    if (!pendingPhoto) {
      setPreviewUrl("");
      return undefined;
    }

    const objectUrl = URL.createObjectURL(pendingPhoto);
    setPreviewUrl(objectUrl);

    return () => URL.revokeObjectURL(objectUrl);
  }, [pendingPhoto]);

  const isTeacher = user?.role === "teacher" || user?.role === "admin";
  const myCourseIds = new Set(myCourses.map((course) => course.id));
  const savingCourse = creating || updating || uploadingThumbnail;
  const normalizedQuery = query.trim().toLowerCase();
  const allCategoryOptions = React.useMemo(() => {
    const map = new Map();
    [...POPULAR_COURSE_CATEGORIES, ...categories]
      .map(normalizeCategory)
      .filter(Boolean)
      .forEach((item) => map.set(item, item));
    return Array.from(map.values());
  }, [categories]);
  const visibleCategoryOptions = React.useMemo(() => {
    if (showAllCategories || allCategoryOptions.length <= 8) return allCategoryOptions;
    return allCategoryOptions.slice(0, 8);
  }, [allCategoryOptions, showAllCategories]);
  const activeFiltersCount = (query.trim() ? 1 : 0) + categoryFilters.length;
  const visibleCourses = React.useMemo(() => {
    return catalogCourses.filter((course) => {
      const normalizedCourseCategory = normalizeCategory(course.category);
      const inCategory = categoryFilters.length === 0 || categoryFilters.includes(normalizedCourseCategory);
      if (!inCategory) return false;
      if (!normalizedQuery) return true;
      const haystack = `${course.title || ""} ${course.description || ""}`.toLowerCase();
      return haystack.includes(normalizedQuery);
    });
  }, [catalogCourses, categoryFilters, normalizedQuery]);

  function resetEditorState() {
    setEditingCourse(null);
    setPendingPhoto(null);
    setPreviewUrl("");
    setPhotoHint("");
    form.resetFields();

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }

  function openCreateDrawer() {
    setEditingCourse(null);
    form.setFieldsValue(defaultCourseValues);
    setPendingPhoto(null);
    setPreviewUrl("");
    setPhotoHint("");
    setEditorOpen(true);
  }

  function openEditDrawer(course) {
    setEditingCourse(course);
    form.setFieldsValue({
      title: course.title,
      description: course.description,
      category: course.category || "",
      is_published: course.is_published,
    });
    setPendingPhoto(null);
    setPreviewUrl("");
    setPhotoHint("");
    setEditorOpen(true);
  }

  function closeEditor() {
    setEditorOpen(false);
    resetEditorState();
  }

  async function openStudentsModal(course) {
    setSelectedCourse(course);
    setStudentsOpen(true);

    try {
      await fetchCourseStudents(course.id);
    } catch (error) {
      message.error(getErrorMessage(error, "Не удалось загрузить список студентов"));
    }
  }

  function closeStudentsModal() {
    setStudentsOpen(false);
    setSelectedCourse(null);
  }

  function preparePhoto(file) {
    if (!file) return;

    if (!["image/jpeg", "image/png"].includes(file.type)) {
      message.error("Поддерживаются только JPG и PNG");
      return;
    }

    setPendingPhoto(file);
    setPhotoHint(file.name ? `Вы выбрали файл: ${file.name}` : "Изображение готово к загрузке.");
    message.info("Проверьте предпросмотр обложки перед сохранением курса.");
  }

  function handlePaste(event) {
    const items = Array.from(event.clipboardData?.items || []);
    const imageItem = items.find((item) => item.type === "image/png" || item.type === "image/jpeg");

    if (!imageItem) return;

    event.preventDefault();
    preparePhoto(imageItem.getAsFile());
  }

  async function handleSubmit(values) {
    try {
      let targetCourse = editingCourse;

      if (editingCourse) {
        targetCourse = await submitUpdate({
          courseId: editingCourse.id,
          payload: values,
        });
      } else {
        targetCourse = await submitCreate(values);
      }

      if (pendingPhoto && targetCourse?.id) {
        await submitUploadThumbnail({
          courseId: targetCourse.id,
          file: pendingPhoto,
        });
      }

      message.success(editingCourse ? "Курс обновлен" : "Курс создан");
      closeEditor();
    } catch (error) {
      message.error(getErrorMessage(error, "Не удалось сохранить курс"));
    }
  }

  async function handleEnroll(courseId) {
    Modal.confirm({
      title: "Записаться на курс?",
      content: "Курс будет добавлен в раздел «Мои курсы». Вы сможете продолжить обучение в любое время.",
      okText: "Да, записаться",
      cancelText: "Отмена",
      onOk: async () => {
        try {
          await submitEnroll(courseId);
          message.success("Вы записались на курс");
        } catch (error) {
          message.error(getErrorMessage(error, "Не удалось записаться на курс"));
        }
      },
    });
  }

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

  async function handleDelete(courseId) {
    try {
      await submitDelete(courseId);
      message.success("Курс удален");
    } catch (error) {
      message.error(getErrorMessage(error, "Не удалось удалить курс"));
    }
  }

  async function handleRemoveStudent(studentId) {
    if (!selectedCourse?.id || !studentId || studentId === "undefined") return;

    try {
      await submitRemoveStudent({
        courseId: selectedCourse.id,
        studentId,
      });
      message.success("Студент удален с курса");
    } catch (error) {
      message.error(getErrorMessage(error, "Не удалось удалить студента с курса"));
    }
  }

  function renderCourseActions(course, isOwnCourse, alreadyInMyCourses) {
    return (
      <Space wrap>
        <Button>
          <Link to={`/courses/${course.id}`}>Открыть курс</Link>
        </Button>
        {isOwnCourse || alreadyInMyCourses ? (
          <Button>
            <Link to="/my-courses">Открыть в моих курсах</Link>
          </Button>
        ) : null}

        {isOwnCourse ? (
          <>
            <Button icon={<TeamOutlined />} onClick={() => openStudentsModal(course)}>
              Студенты
            </Button>
            <Button icon={<EditOutlined />} onClick={() => openEditDrawer(course)}>
              Редактировать
            </Button>
            <Button
              type={course.is_published ? "default" : "primary"}
              icon={course.is_published ? <EyeInvisibleOutlined /> : <UploadOutlined />}
              loading={updating}
              onClick={() => handlePublishToggle(course)}
            >
              {course.is_published ? "Снять с публикации" : "Опубликовать"}
            </Button>
            <Popconfirm
              title="Удалить курс?"
              description="Курс и связанные с ним материалы будут удалены без возможности восстановления."
              okText="Удалить"
              cancelText="Отмена"
              okButtonProps={{ danger: true, loading: deleting }}
              onConfirm={() => handleDelete(course.id)}
            >
              <Button danger icon={<DeleteOutlined />}>
                Удалить
              </Button>
            </Popconfirm>
          </>
        ) : null}

        {!isTeacher && !alreadyInMyCourses ? (
          <Button type="primary" loading={enrolling} onClick={() => handleEnroll(course.id)}>
            Записаться
          </Button>
        ) : null}
      </Space>
    );
  }

  function toggleCategoryFilter(category) {
    setCategoryFilters((prev) => (prev.includes(category) ? prev.filter((item) => item !== category) : [...prev, category]));
  }

  function resetFilters() {
    setQuery("");
    setCategoryFilters([]);
  }

  return (
    <AppShell
      title="Каталог курсов"
      subtitle={
        isTeacher
          ? "Создание, редактирование и публикация курсов."
          : "Просмотр опубликованных курсов и запись на обучение."
      }
    >
      <div className="page-toolbar">
        <Typography.Paragraph className="panel-copy toolbar-copy">
          {isTeacher
            ? "Управляйте курсами и состоянием публикации."
            : 'После записи курс появится во вкладке "Мои курсы".'}
        </Typography.Paragraph>
        {isTeacher ? (
          <Button type="primary" icon={<PlusOutlined />} onClick={openCreateDrawer}>
            Создать курс
          </Button>
        ) : null}
      </div>

      <Card className="panel-card courses-filters-card">
        <Space direction="vertical" size={14} style={{ width: "100%" }}>
          <div className="courses-filters-head">
            <Badge count={activeFiltersCount} size="small" color="#0f766e">
              <Typography.Text strong>
                <FilterOutlined /> Фильтры
              </Typography.Text>
            </Badge>
            <Button
              size="small"
              icon={<CloseCircleOutlined />}
              onClick={resetFilters}
              disabled={activeFiltersCount === 0}
            >
              Сбросить
            </Button>
          </div>

          <Input
            allowClear
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Поиск по названию и описанию"
            prefix={<SearchOutlined />}
            size="large"
          />

          <div className="courses-categories-wrap">
            {visibleCategoryOptions.map((category) => (
              <Tag.CheckableTag
                key={category}
                checked={categoryFilters.includes(category)}
                onChange={() => toggleCategoryFilter(category)}
              >
                {category}
              </Tag.CheckableTag>
            ))}
            {allCategoryOptions.length > 8 ? (
              <Button type="link" size="small" onClick={() => setShowAllCategories((value) => !value)}>
                {showAllCategories ? "Свернуть" : "Показать все"}
              </Button>
            ) : null}
          </div>
        </Space>
      </Card>

      <CourseCatalogSection
        courses={visibleCourses}
        catalogPending={catalogPending}
        isTeacher={isTeacher}
        userId={user?.id}
        myCourseIds={myCourseIds}
        renderCourseActions={renderCourseActions}
      />

      <CourseEditorDrawer
        open={editorOpen}
        editingCourse={editingCourse}
        form={form}
        defaultCourseValues={defaultCourseValues}
        onClose={closeEditor}
        onSubmit={handleSubmit}
        onPreparePhoto={preparePhoto}
        onPaste={handlePaste}
        onShowPasteHint={() => message.info("Скопируйте изображение и нажмите Ctrl+V внутри блока обложки.")}
        savingCourse={savingCourse}
        pendingPhoto={pendingPhoto}
        photoHint={photoHint}
        previewUrl={previewUrl}
        fileInputRef={fileInputRef}
        categoryOptions={allCategoryOptions}
      />

      <CourseStudentsModal
        open={studentsOpen}
        selectedCourse={selectedCourse}
        courseStudents={courseStudents}
        courseStudentsPending={courseStudentsPending}
        removingStudent={removingStudent}
        onClose={closeStudentsModal}
        onRemoveStudent={handleRemoveStudent}
      />
    </AppShell>
  );
}

