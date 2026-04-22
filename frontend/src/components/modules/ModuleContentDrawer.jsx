import React from "react";
import { Alert, Button, Drawer, Form, Input, Radio, Space, Typography } from "antd";

export function ModuleContentDrawer({
  open,
  form,
  defaultValues,
  contentType,
  fileHint,
  isEditing,
  replacingFile,
  savingContent,
  fileInputRef,
  onClose,
  onSubmit,
  onPrepareFile,
}) {
  const isFileContent = contentType === "video" || contentType === "pdf" || contentType === "presentation";
  const showFilePicker = isFileContent;

  function getAccept() {
    if (contentType === "video") return "video/mp4,video/webm";
    if (contentType === "pdf") return "application/pdf";
    if (contentType === "presentation") {
      return "application/vnd.openxmlformats-officedocument.presentationml.presentation,.pptx";
    }
    return "";
  }

  function getFileCopy() {
    if (contentType === "video") {
      return "Загрузите видео в формате MP4 или WEBM.";
    }
    if (contentType === "pdf") {
      return "Загрузите PDF-файл, который студент сможет читать прямо в модуле.";
    }
    return "Загрузите PPTX-презентацию. Студент сможет листать слайды прямо внутри модуля без перехода на внешний сервис.";
  }

  return (
    <Drawer title={isEditing ? "Редактирование материала" : "Новый блок контента"} width={560} onClose={onClose} open={open}>
      <Form form={form} layout="vertical" onFinish={onSubmit} initialValues={defaultValues}>
        <Form.Item name="content_type" label="Тип контента">
          <Radio.Group disabled={isEditing}>
            <Radio.Button value="text">Текст</Radio.Button>
            <Radio.Button value="video">Видео</Radio.Button>
            <Radio.Button value="pdf">PDF</Radio.Button>
            <Radio.Button value="presentation">Презентация</Radio.Button>
            <Radio.Button value="link">Ссылка</Radio.Button>
          </Radio.Group>
        </Form.Item>

        <Form.Item
          name="title"
          label="Заголовок блока"
          rules={[{ required: true, message: "Введите заголовок блока" }]}
        >
          <Input placeholder="Например, Теоретическая часть" />
        </Form.Item>

        {contentType === "text" ? (
          <Form.Item
            name="text_content"
            label="Текст"
            rules={[{ required: true, message: "Введите текст блока" }]}
          >
            <Input.TextArea rows={8} placeholder="Основной текст урока" />
          </Form.Item>
        ) : null}

        {contentType === "link" ? (
          <Form.Item
            name="source_url"
            label="Ссылка на ресурс"
            rules={[{ required: true, message: "Укажите ссылку" }]}
          >
            <Input placeholder="https://..." />
          </Form.Item>
        ) : null}

        {showFilePicker ? (
          <div className="content-upload-box">
            <Typography.Paragraph className="panel-copy">
              {isEditing
                ? "Можно оставить текущий файл как есть или выбрать новый, чтобы заменить его в этом блоке."
                : getFileCopy()}
            </Typography.Paragraph>
            <input
              ref={fileInputRef}
              type="file"
              accept={getAccept()}
              className="hidden-file-input"
              onChange={(event) => onPrepareFile(event.target.files?.[0] || null)}
            />
            <Space wrap>
              <Button onClick={() => fileInputRef.current?.click()}>
                {isEditing ? "Заменить файл" : "Выбрать файл"}
              </Button>
            </Space>
            {fileHint ? <Alert className="photo-status-alert" type="info" showIcon message={fileHint} /> : null}
          </div>
        ) : null}

        <Space wrap>
          <Button type="primary" htmlType="submit" loading={savingContent || replacingFile}>
            {isEditing ? "Сохранить изменения" : "Сохранить блок"}
          </Button>
          <Button onClick={onClose}>Отмена</Button>
        </Space>
      </Form>
    </Drawer>
  );
}
