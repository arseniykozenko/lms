import React from "react";
import { Button, Drawer, Form, Input, Radio, Space, Typography } from "antd";

export function CourseModuleDrawer({
  open,
  editingModule,
  form,
  defaultModuleValues,
  savingModule,
  onClose,
  onSubmit,
}) {
  return (
    <Drawer
      title={editingModule ? "Редактирование модуля" : "Новый модуль"}
      width={540}
      onClose={onClose}
      open={open}
    >
      <Form form={form} layout="vertical" onFinish={onSubmit} initialValues={defaultModuleValues}>
        <Form.Item
          name="title"
          label="Название модуля"
          rules={[{ required: true, message: "Введите название модуля" }]}
        >
          <Input placeholder="Например, Введение в курс" />
        </Form.Item>
        <Form.Item name="description" label="Описание">
          <Input.TextArea rows={5} placeholder="Кратко опишите, что изучит студент в этом модуле" />
        </Form.Item>
        <Form.Item name="is_published" label="Статус">
          <Radio.Group>
            <Radio.Button value={false}>Черновик</Radio.Button>
            <Radio.Button value>Опубликовать</Radio.Button>
          </Radio.Group>
        </Form.Item>
        <Typography.Paragraph className="panel-copy module-drawer-note">
          Контент модуля добавляется уже внутри страницы модуля. Там преподаватель сможет загрузить видео, PDF,
          текстовые блоки и встроенные материалы.
        </Typography.Paragraph>
        <Space wrap>
          <Button type="primary" htmlType="submit" loading={savingModule}>
            {editingModule ? "Сохранить модуль" : "Создать модуль"}
          </Button>
          <Button onClick={onClose}>Отмена</Button>
        </Space>
      </Form>
    </Drawer>
  );
}
