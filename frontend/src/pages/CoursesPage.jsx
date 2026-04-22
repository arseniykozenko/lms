import React from "react";
import {
  DeleteOutlined,
  EditOutlined,
  EyeInvisibleOutlined,
  PlusOutlined,
  TeamOutlined,
  UploadOutlined,
} from "@ant-design/icons";
import { Button, Form, Popconfirm, Space, Typography, message } from "antd";
import { useUnit } from "effector-react";
import { Link } from "react-router-dom";

import { AppShell } from "../components/AppShell";
import { CourseCatalogSection } from "../components/courses/CourseCatalogSection";
import { CourseEditorDrawer } from "../components/courses/CourseEditorDrawer";
import { CourseStudentsModal } from "../components/courses/CourseStudentsModal";
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
  removeCourseStudentFx,
  updateCourseFx,
  uploadCourseThumbnailFx,
} from "../models/courses";

const defaultCourseValues = {
  title: "",
  description: "",
  is_free: true,
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
    removeCourseStudentFx,
  ]);

  const [editorOpen, setEditorOpen] = React.useState(false);
  const [studentsOpen, setStudentsOpen] = React.useState(false);
  const [editingCourse, setEditingCourse] = React.useState(null);
  const [selectedCourse, setSelectedCourse] = React.useState(null);
  const [pendingPhoto, setPendingPhoto] = React.useState(null);
  const [previewUrl, setPreviewUrl] = React.useState("");
  const [photoHint, setPhotoHint] = React.useState("");
  const fileInputRef = React.useRef(null);
  const [form] = Form.useForm();

  React.useEffect(() => {
    openPage();
  }, [openPage]);

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
      is_free: course.is_free,
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
      message.error(error?.response?.data?.detail || "Не удалось загрузить список студентов");
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
      message.error(error?.response?.data?.detail || "Не удалось сохранить курс");
    }
  }

  async function handleEnroll(courseId) {
    try {
      await submitEnroll(courseId);
      message.success("Вы записались на курс");
    } catch (error) {
      message.error(error?.response?.data?.detail || "Не удалось записаться на курс");
    }
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
      message.error(error?.response?.data?.detail || "Не удалось изменить статус курса");
    }
  }

  async function handleDelete(courseId) {
    try {
      await submitDelete(courseId);
      message.success("Курс удален");
    } catch (error) {
      message.error(error?.response?.data?.detail || "Не удалось удалить курс");
    }
  }

  async function handleRemoveStudent(studentId) {
    if (!selectedCourse) return;

    try {
      await submitRemoveStudent({
        courseId: selectedCourse.id,
        studentId,
      });
      message.success("Студент удален с курса");
    } catch (error) {
      message.error(error?.response?.data?.detail || "Не удалось удалить студента с курса");
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

  return (
    <AppShell
      title="Каталог курсов"
      subtitle={
        isTeacher
          ? "Создавайте новые курсы, редактируйте их и публикуйте для студентов."
          : "Выбирайте опубликованные курсы и записывайтесь на обучение."
      }
    >
      <div className="page-toolbar">
        <Typography.Paragraph className="panel-copy toolbar-copy">
          {isTeacher
            ? "Здесь можно управлять курсами целиком: создавать, редактировать, менять обложку, публиковать, смотреть список студентов и удалять курс."
            : 'После записи курс сразу появится во вкладке "Мои курсы".'}
        </Typography.Paragraph>
        {isTeacher ? (
          <Button type="primary" icon={<PlusOutlined />} onClick={openCreateDrawer}>
            Создать курс
          </Button>
        ) : null}
      </div>

      <CourseCatalogSection
        courses={catalogCourses}
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
