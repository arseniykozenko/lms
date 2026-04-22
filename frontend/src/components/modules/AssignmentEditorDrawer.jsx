import React from "react";
import { Button, Drawer, Form, Input, InputNumber, Switch, Typography } from "antd";

import { AttachmentList } from "../shared/AttachmentList";
import { MarkdownEditor } from "../shared/MarkdownEditor";

export function AssignmentEditorDrawer({
  open,
  form,
  isEditing,
  saving,
  attachments,
  selectedFiles,
  fileInputRef,
  onClose,
  onSubmit,
  onPrepareFiles,
}) {
  return (
    <Drawer
      title={isEditing ? "Редактирование задания" : "Новое задание"}
      width={640}
      open={open}
      onClose={onClose}
      destroyOnClose
    >
      <Form layout="vertical" form={form} onFinish={onSubmit}>
        <Form.Item name="title" label="Название задания" rules={[{ required: true, message: "Введите название задания" }]}>
          <Input placeholder="Например, разбор кейса или итоговое эссе" />
        </Form.Item>

        <Form.Item
          name="instructions_markdown"
          label="Условие задания"
          rules={[{ required: true, message: "Добавьте описание задания" }]}
        >
          <MarkdownEditor
            placeholder="Опишите, что студенту нужно сделать, на что обратить внимание и что приложить в ответе."
            rows={12}
            minHeight={280}
          />
        </Form.Item>

        <div className="assignment-editor-grid">
          <Form.Item name="max_score" label="Максимальный балл">
            <InputNumber min={0} max={100} style={{ width: "100%" }} placeholder="Например, 100" />
          </Form.Item>

          <Form.Item name="is_published" label="Опубликовать сразу" valuePropName="checked">
            <Switch />
          </Form.Item>
        </div>

        <Form.Item label="Файлы задания">
          <div className="assignment-file-picker">
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.zip,.rar,.7z,.pptx,.doc,.docx,.txt"
              multiple
              hidden
              onChange={(event) => onPrepareFiles(event.target.files)}
            />
            <div className="assignment-file-picker-actions">
              <Typography.Text type="secondary">
                Можно приложить несколько файлов: PDF, архивы, презентации и документы.
              </Typography.Text>
              <Button onClick={() => fileInputRef.current?.click()}>Выбрать файлы</Button>
            </div>

            {selectedFiles.length ? (
              <div className="attachment-list">
                {selectedFiles.map((file) => (
                  <Typography.Text key={`${file.name}-${file.size}`}>{file.name}</Typography.Text>
                ))}
              </div>
            ) : (attachments || []).length ? (
              <AttachmentList attachments={attachments} />
            ) : null}
          </div>
        </Form.Item>

        <div className="drawer-actions">
          <Button onClick={onClose}>Отмена</Button>
          <Button type="primary" htmlType="submit" loading={saving}>
            {isEditing ? "Сохранить задание" : "Создать задание"}
          </Button>
        </div>
      </Form>
    </Drawer>
  );
}
