import React from "react";
import { LeftOutlined, PlusOutlined, RightOutlined } from "@ant-design/icons";
import { Alert, Button, Card, Divider, Drawer, Form, Input, Radio, Space, Typography } from "antd";

export function ModuleQuizDrawer({
  open,
  form,
  defaultValues,
  savingQuiz,
  isEditing,
  questionsLocked,
  onClose,
  onSubmit,
}) {
  const questions = Form.useWatch("questions", form) || defaultValues.questions;
  const [currentQuestionIndex, setCurrentQuestionIndex] = React.useState(0);

  React.useEffect(() => {
    if (open) {
      setCurrentQuestionIndex(0);
    }
  }, [open]);

  return (
    <Drawer title={isEditing ? "Редактирование квиза" : "Создание квиза"} width={720} onClose={onClose} open={open}>
      <Form form={form} layout="vertical" onFinish={onSubmit} initialValues={defaultValues}>
        <Form.Item
          name="title"
          label="Название квиза"
          rules={[{ required: true, message: "Введите название квиза" }]}
        >
          <Input placeholder="Например, Проверка по теме модуля" />
        </Form.Item>
        <Form.Item name="is_published" label="Статус">
          <Radio.Group>
            <Radio.Button value={false}>Черновик</Radio.Button>
            <Radio.Button value>Опубликовать</Radio.Button>
          </Radio.Group>
        </Form.Item>

        {questionsLocked ? (
          <Alert
            type="info"
            showIcon
            message="По этому квизу уже есть попытки"
            description="Можно менять только название и статус публикации. Вопросы и правильные ответы зафиксированы, чтобы не сломать историю результатов."
            style={{ marginBottom: 16 }}
          />
        ) : null}

        <Form.List name="questions">
          {(fields, { add, remove }) => {
            const currentField = fields[currentQuestionIndex];

            return (
              <Space direction="vertical" size={16} className="quiz-builder-stack">
                <div className="quiz-builder-header">
                  <div>
                    <Typography.Title level={5} className="quiz-builder-progress-title">
                      Вопрос {fields.length ? currentQuestionIndex + 1 : 0} из {fields.length}
                    </Typography.Title>
                    <Typography.Paragraph className="panel-copy quiz-builder-progress-copy">
                      Заполняйте квиз последовательно, как отдельные шаги. Так структура ощущается намного чище.
                    </Typography.Paragraph>
                  </div>
                  <Space wrap>
                    <Button
                      icon={<PlusOutlined />}
                      disabled={questionsLocked}
                      onClick={() => {
                        add({ content: "", options: ["", ""], correct_option: "", explanation: "" });
                        setCurrentQuestionIndex(fields.length);
                      }}
                    >
                      Добавить вопрос
                    </Button>
                    {fields.length > 1 ? (
                      <Button
                        danger
                        disabled={questionsLocked}
                        onClick={() => {
                          remove(currentField.name);
                          setCurrentQuestionIndex((index) => Math.max(0, Math.min(index - 1, fields.length - 2)));
                        }}
                      >
                        Удалить текущий
                      </Button>
                    ) : null}
                  </Space>
                </div>

                {currentField ? (
                  <Card className="quiz-builder-card" title={`Вопрос ${currentQuestionIndex + 1}`}>
                    <Form.Item
                      name={[currentField.name, "content"]}
                      label="Текст вопроса"
                      rules={[{ required: true, message: "Введите текст вопроса" }]}
                    >
                      <Input.TextArea rows={3} placeholder="Сформулируйте вопрос" disabled={questionsLocked} />
                    </Form.Item>

                    <Form.List name={[currentField.name, "options"]}>
                      {(optionFields, optionOps) => (
                        <Space direction="vertical" size={12} className="quiz-builder-options">
                          {optionFields.map((optionField, optionIndex) => (
                            <Form.Item
                              key={optionField.key}
                              name={optionField.name}
                              label={`Вариант ${optionIndex + 1}`}
                              rules={[{ required: true, message: "Введите вариант ответа" }]}
                            >
                              <Input
                                disabled={questionsLocked}
                                placeholder={`Вариант ответа ${optionIndex + 1}`}
                                addonAfter={
                                  optionFields.length > 2 && !questionsLocked ? (
                                    <Button type="link" danger onClick={() => optionOps.remove(optionField.name)}>
                                      Удалить
                                    </Button>
                                  ) : null
                                }
                              />
                            </Form.Item>
                          ))}
                          <Button disabled={questionsLocked} onClick={() => optionOps.add("")}>Добавить вариант</Button>
                        </Space>
                      )}
                    </Form.List>

                    <Form.Item
                      name={[currentField.name, "correct_option"]}
                      label="Правильный ответ"
                      rules={[{ required: true, message: "Укажите правильный вариант точно как в списке выше" }]}
                    >
                      <Input placeholder="Текст правильного варианта" disabled={questionsLocked} />
                    </Form.Item>

                    <Form.Item name={[currentField.name, "explanation"]} label="Пояснение после ответа">
                      <Input.TextArea rows={3} placeholder="Коротко объясните правильный ответ" disabled={questionsLocked} />
                    </Form.Item>
                  </Card>
                ) : null}

                <div className="quiz-builder-footer-nav">
                  <Button
                    icon={<LeftOutlined />}
                    disabled={currentQuestionIndex === 0}
                    onClick={() => setCurrentQuestionIndex((index) => Math.max(0, index - 1))}
                  >
                    Предыдущий вопрос
                  </Button>
                  <Button
                    icon={<RightOutlined />}
                    iconPosition="end"
                    disabled={currentQuestionIndex >= fields.length - 1}
                    onClick={() => setCurrentQuestionIndex((index) => Math.min(fields.length - 1, index + 1))}
                  >
                    Следующий вопрос
                  </Button>
                </div>
              </Space>
            );
          }}
        </Form.List>

        <Divider />
        <Space wrap>
          <Button type="primary" htmlType="submit" loading={savingQuiz}>
            {isEditing ? "Сохранить изменения" : "Сохранить квиз"}
          </Button>
          <Button onClick={onClose}>Отмена</Button>
        </Space>
      </Form>
    </Drawer>
  );
}
