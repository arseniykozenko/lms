import React, { useEffect, useRef, useState } from "react";
import { UserOutlined } from "@ant-design/icons";
import { Button, Card, Col, Form, Input, Row, Statistic, message } from "antd";
import { useUnit } from "effector-react";

import { AppShell } from "../components/AppShell";
import { getErrorMessage } from "../lib/errors";
import { isTeacherRole, roleLabel } from "../lib/roles";
import { getUserDisplayName } from "../lib/userName";
import { ProfileHeroCard } from "../components/profile/ProfileHeroCard";
import { ProfilePhotoEditor } from "../components/profile/ProfilePhotoEditor";
import {
  $courses,
  $photoPending,
  $profilePending,
  $user,
  saveProfileFx,
  saveProfilePhotoFx,
} from "../models/auth";

export function ProfilePage() {
  const [user, courses, saving, uploading, saveProfile, savePhoto] = useUnit([
    $user,
    $courses,
    $profilePending,
    $photoPending,
    saveProfileFx,
    saveProfilePhotoFx,
  ]);

  const [pendingPhoto, setPendingPhoto] = useState(null);
  const [previewUrl, setPreviewUrl] = useState("");
  const [photoHint, setPhotoHint] = useState("");
  const fileInputRef = useRef(null);

  useEffect(() => {
    if (!pendingPhoto) {
      setPreviewUrl("");
      return;
    }

    const objectUrl = URL.createObjectURL(pendingPhoto);
    setPreviewUrl(objectUrl);

    return () => URL.revokeObjectURL(objectUrl);
  }, [pendingPhoto]);

  async function handleSave(values) {
    try {
      await saveProfile(values);
      message.success("Профиль обновлен");
    } catch (error) {
      message.error(getErrorMessage(error, "Не удалось обновить профиль"));
    }
  }

  function preparePhoto(file) {
    if (!file) return;

    if (!["image/jpeg", "image/png"].includes(file.type)) {
      message.error("Поддерживаются только JPG и PNG");
      return;
    }

    setPendingPhoto(file);
    setPhotoHint(file.name ? `Вы выбрали файл: ${file.name}` : "Изображение готово к загрузке.");
    message.info("Проверьте предпросмотр и подтвердите смену фото.");
  }

  async function confirmPhotoUpload() {
    if (!pendingPhoto) return;

    try {
      await savePhoto(pendingPhoto);
      setPendingPhoto(null);
      setPhotoHint("");

      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }

      message.success("Фото профиля обновлено");
    } catch (error) {
      message.error(getErrorMessage(error, "Не удалось загрузить фото"));
    }
  }

  function cancelPendingPhoto() {
    setPendingPhoto(null);
    setPhotoHint("");

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }

  function handlePaste(event) {
    const items = Array.from(event.clipboardData?.items || []);
    const imageItem = items.find((item) => item.type === "image/png" || item.type === "image/jpeg");

    if (!imageItem) return;

    event.preventDefault();
    preparePhoto(imageItem.getAsFile());
  }

  const isTeacher = isTeacherRole(user?.role);
  const displayPhoto = previewUrl || user?.profile_photo_url || undefined;

  return (
    <AppShell
      title="Профиль"
      subtitle={
        isTeacher
          ? "Управляйте преподавательским профилем и публичной информацией."
          : "Управляйте персональными данными и видимостью профиля."
      }
    >
      <Row gutter={[20, 20]}>
        <Col xs={24} xl={8}>
          <ProfileHeroCard
            displayPhoto={displayPhoto}
            fullName={getUserDisplayName(user)}
            email={user?.email}
            role={user?.role}
          />
        </Col>

        <Col xs={24} xl={16}>
          <Card className="panel-card" title="Редактирование профиля">
            <Row gutter={[20, 20]}>
              <Col xs={24} md={10}>
                <ProfilePhotoEditor
                  displayPhoto={displayPhoto}
                  fileInputRef={fileInputRef}
                  onPreparePhoto={preparePhoto}
                  onPaste={handlePaste}
                  photoHint={photoHint}
                  pendingPhoto={pendingPhoto}
                  previewUrl={previewUrl}
                  uploading={uploading}
                  onConfirmUpload={confirmPhotoUpload}
                  onCancelPendingPhoto={cancelPendingPhoto}
                />
              </Col>

              <Col xs={24} md={14}>
                <Form
                  layout="vertical"
                  initialValues={{ first_name: user?.first_name, second_name: user?.second_name }}
                  onFinish={handleSave}
                  key={user?.id || user?.email}
                >
                  <Form.Item name="first_name" label="Имя" rules={[{ required: true, message: "Введите имя" }]}>
                    <Input prefix={<UserOutlined />} placeholder="Ваше имя" />
                  </Form.Item>
                  <Form.Item name="second_name" label="Фамилия" rules={[{ required: true, message: "Введите фамилию" }]}>
                    <Input prefix={<UserOutlined />} placeholder="Ваша фамилия" />
                  </Form.Item>

                  <Button type="primary" htmlType="submit" loading={saving}>
                    Сохранить изменения
                  </Button>
                </Form>
              </Col>
            </Row>
          </Card>
        </Col>

        <Col xs={24} md={8}>
          <Card className="metric-card">
            <Statistic title={isTeacher ? "Готовность профиля" : "Учебный доступ"} value={user?.is_active ? "Включен" : "Выключен"} />
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card className="metric-card">
            <Statistic title={isTeacher ? "Курсов под контролем" : "Курсов подключено"} value={courses.length} />
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card className="metric-card">
            <Statistic title="Роль аккаунта" value={roleLabel(user?.role)} />
          </Card>
        </Col>
      </Row>
    </AppShell>
  );
}
