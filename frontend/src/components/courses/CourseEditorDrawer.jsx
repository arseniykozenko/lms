import React from "react";
import { BookOutlined, CameraOutlined } from "@ant-design/icons";
import { Alert, Button, Col, Drawer, Form, Input, Radio, Row, Space, Typography } from "antd";

export function CourseEditorDrawer({
  open,
  editingCourse,
  form,
  defaultCourseValues,
  onClose,
  onSubmit,
  onPreparePhoto,
  onPaste,
  onShowPasteHint,
  savingCourse,
  pendingPhoto,
  photoHint,
  previewUrl,
  fileInputRef,
  categoryOptions = [],
}) {
  const editorPreviewUrl = previewUrl || editingCourse?.thumbnail_url || "";
  const selectedCategory = Form.useWatch("category", form);

  function handleCategoryPresetChange(event) {
    const next = event?.target?.value || "";
    form.setFieldValue("category", next);
  }

  return (
    <Drawer
      title={editingCourse ? "Редактирование курса" : "Новый курс"}
      width={760}
      onClose={onClose}
      open={open}
    >
      <Row gutter={[20, 20]}>
        <Col xs={24} md={10}>
          <div className="inline-photo-editor course-cover-editor" tabIndex={0} onPaste={onPaste}>
            <div
              className="course-editor-preview"
              style={
                editorPreviewUrl
                  ? {
                      backgroundImage: `linear-gradient(rgba(16,36,31,0.14), rgba(16,36,31,0.14)), url(${editorPreviewUrl})`,
                    }
                  : undefined
              }
            >
              {!editorPreviewUrl ? <BookOutlined className="course-card-cover-icon" /> : null}
            </div>
            <Typography.Title level={5} className="inline-photo-title">
              Обложка курса
            </Typography.Title>
            <Typography.Paragraph className="panel-copy inline-photo-copy">
              Загрузите JPG или PNG с компьютера либо вставьте изображение из буфера обмена через Ctrl+V.
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
              <Button onClick={onShowPasteHint}>Вставить обложку</Button>
            </Space>

            {photoHint ? <Alert className="photo-status-alert" type="info" showIcon message={photoHint} /> : null}

            {pendingPhoto ? (
              <div className="photo-confirm-box">
                <Typography.Text strong>Новая обложка готова к сохранению</Typography.Text>
                <div className="photo-file-name">{pendingPhoto.name || "Изображение из буфера обмена"}</div>
                <Typography.Paragraph className="panel-copy course-editor-confirm-copy">
                  Обложка загрузится вместе с сохранением курса.
                </Typography.Paragraph>
              </div>
            ) : null}
          </div>
        </Col>

        <Col xs={24} md={14}>
          <Form form={form} layout="vertical" onFinish={onSubmit} initialValues={defaultCourseValues}>
            <Form.Item
              name="title"
              label="Название курса"
              rules={[{ required: true, message: "Введите название курса" }]}
            >
              <Input placeholder="Например, Основы программирования" />
            </Form.Item>
            <Form.Item
              name="description"
              label="Описание"
              rules={[{ required: true, message: "Введите описание курса" }]}
            >
              <Input.TextArea rows={6} placeholder="Кратко опишите пользу и структуру курса" />
            </Form.Item>
            <Form.Item label="Популярные категории">
              <Radio.Group value={selectedCategory || undefined} onChange={handleCategoryPresetChange}>
                <Space size={[8, 8]} wrap>
                  {categoryOptions.map((value) => (
                    <Radio.Button key={value} value={value}>
                      {value}
                    </Radio.Button>
                  ))}
                </Space>
              </Radio.Group>
            </Form.Item>
            <Form.Item name="category" label="Своя категория">
              <Input placeholder="Например, Программирование" allowClear />
            </Form.Item>
            <Form.Item name="is_published" label="Статус">
              <Radio.Group>
                <Radio.Button value={false}>Черновик</Radio.Button>
                <Radio.Button value>Опубликовать</Radio.Button>
              </Radio.Group>
            </Form.Item>
            <Space wrap className="course-editor-actions">
              <Button type="primary" htmlType="submit" loading={savingCourse}>
                {editingCourse ? "Сохранить курс" : "Создать курс"}
              </Button>
              <Button onClick={onClose}>Отмена</Button>
            </Space>
          </Form>
        </Col>
      </Row>
    </Drawer>
  );
}
