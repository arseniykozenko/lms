import React from "react";
import { CameraOutlined, UserOutlined } from "@ant-design/icons";
import { Alert, Avatar, Button, Space, Typography, message } from "antd";

export function ProfilePhotoEditor({
  displayPhoto,
  fileInputRef,
  onPreparePhoto,
  onPaste,
  photoHint,
  pendingPhoto,
  previewUrl,
  uploading,
  onConfirmUpload,
  onCancelPendingPhoto,
}) {
  return (
    <div className="inline-photo-editor" tabIndex={0} onPaste={onPaste}>
      <Avatar size={112} icon={<UserOutlined />} src={displayPhoto} />
      <Typography.Title level={5} className="inline-photo-title">
        Фото профиля
      </Typography.Title>
      <Typography.Paragraph className="panel-copy inline-photo-copy">
        Выберите JPG или PNG с компьютера либо вставьте изображение из буфера обмена через Ctrl+V.
      </Typography.Paragraph>

      <input
        ref={fileInputRef}
        type="file"
        accept="image/png,image/jpeg"
        className="hidden-file-input"
        onChange={(event) => onPreparePhoto(event.target.files?.[0] || null)}
      />

      <Space wrap className="inline-photo-actions">
        <Button icon={<CameraOutlined />} onClick={() => fileInputRef.current?.click()}>
          Выбрать файл
        </Button>
        <Button onClick={() => message.info("Скопируйте изображение и нажмите Ctrl+V внутри блока с фото.")}>
          Вставить фото
        </Button>
      </Space>

      {photoHint ? <Alert className="photo-status-alert" type="info" showIcon message={photoHint} /> : null}

      {pendingPhoto ? (
        <div className="photo-confirm-box">
          <Typography.Text strong>Новое фото готово к загрузке</Typography.Text>
          <div className="photo-file-name">{pendingPhoto.name || "Изображение из буфера обмена"}</div>
          <div className="photo-preview-frame">
            <Avatar size={132} icon={<UserOutlined />} src={previewUrl} />
          </div>
          <Space wrap>
            <Button type="primary" loading={uploading} onClick={onConfirmUpload}>
              Сохранить фото
            </Button>
            <Button onClick={onCancelPendingPhoto}>Отменить</Button>
          </Space>
        </div>
      ) : null}
    </div>
  );
}
