import React from "react";
import { LeftOutlined, ReadOutlined, RightOutlined } from "@ant-design/icons";
import { Alert, Button, Card, Empty, Form, List, Modal, Popconfirm, Progress, Radio, Skeleton, Space, Tag, Typography, message } from "antd";

import { formatDate, formatDeadline, isDeadlinePassed } from "./moduleHelpers";

export function ModuleQuizPanel({
  quiz,
  quizPending,
  canManageModule,
  canTakeQuiz,
  attempts,
  quizSubmitResult,
  submittingQuiz,
  deletingQuiz,
  quizAnswerForm,
  onDeleteQuiz,
  onEditQuiz,
  onSubmitQuiz,
  onRestartAttempt,
  onOpenQuizDrawer,
}) {
  const [currentQuestionIndex, setCurrentQuestionIndex] = React.useState(0);
  const [answerSnapshot, setAnswerSnapshot] = React.useState({});
  const [confirmOpen, setConfirmOpen] = React.useState(false);

  React.useEffect(() => {
    setCurrentQuestionIndex(0);
    setConfirmOpen(false);
  }, [quiz?.id, quizSubmitResult?.id]);

  const readAllAnswers = React.useCallback(() => {
    const storedAnswers = quizAnswerForm.getFieldsValue(true)?.answers || {};
    const normalizedAnswers = {};

    (quiz?.questions || []).forEach((question) => {
      normalizedAnswers[question.id] = storedAnswers[question.id];
    });

    return normalizedAnswers;
  }, [quiz, quizAnswerForm]);

  const syncAnswerSnapshot = React.useCallback(() => {
    const normalizedAnswers = readAllAnswers();
    setAnswerSnapshot(normalizedAnswers);
    return normalizedAnswers;
  }, [readAllAnswers]);

  React.useEffect(() => {
    syncAnswerSnapshot();
  }, [quiz?.id, quizSubmitResult?.id, syncAnswerSnapshot]);

  const totalQuestions = quiz?.questions?.length || 0;
  const currentQuestion = quiz?.questions?.[currentQuestionIndex] || null;
  const answeredCount =
    quiz?.questions?.filter(
      (question) =>
        typeof answerSnapshot?.[question.id] === "string" && answerSnapshot[question.id].trim().length > 0,
    ).length || 0;
  const progressPercent = totalQuestions ? Math.round((answeredCount / totalQuestions) * 100) : 0;
  const hasCompletedAttempt = Boolean(quizSubmitResult?.id);
  const correctCount = quizSubmitResult?.score || 0;
  const incorrectCount = hasCompletedAttempt ? Math.max(totalQuestions - correctCount, 0) : 0;
  const attemptPercent = totalQuestions ? Math.round((correctCount / totalQuestions) * 100) : 0;

  function goToPreviousQuestion() {
    setCurrentQuestionIndex((index) => Math.max(0, index - 1));
  }

  function goToNextQuestion() {
    setCurrentQuestionIndex((index) => Math.min(totalQuestions - 1, index + 1));
  }

  function requestSubmitQuiz() {
    const normalizedAnswers = syncAnswerSnapshot();
    const firstUnansweredIndex = quiz.questions.findIndex(
      (question) =>
        typeof normalizedAnswers?.[question.id] !== "string" || normalizedAnswers[question.id].trim().length === 0,
    );

    if (firstUnansweredIndex !== -1) {
      setCurrentQuestionIndex(firstUnansweredIndex);
      message.warning("Перед завершением теста нужно ответить на все вопросы");
      return;
    }

    setConfirmOpen(true);
  }

  async function handleConfirmSubmit() {
    const normalizedAnswers = syncAnswerSnapshot();
    await onSubmitQuiz({ answers: normalizedAnswers });
    setConfirmOpen(false);
  }

  return (
    <>
      <Card
        className="panel-card"
        title={
          <Space>
            <ReadOutlined />
            <span>Тест по модулю</span>
          </Space>
        }
        extra={
          canManageModule ? (
            !quiz ? (
              <Button type="link" onClick={onOpenQuizDrawer}>
                Создать квиз
              </Button>
            ) : (
              <Space size={4}>
                <Button type="link" onClick={onEditQuiz}>
                  Изменить
                </Button>
                <Popconfirm
                  title="Удалить квиз?"
                  description="Это действие доступно только пока по квизу нет попыток."
                  okText="Удалить"
                  cancelText="Отмена"
                  onConfirm={onDeleteQuiz}
                  disabled={quiz.has_attempts}
                >
                  <Button type="link" danger loading={deletingQuiz} disabled={quiz.has_attempts}>
                    Удалить
                  </Button>
                </Popconfirm>
              </Space>
            )
          ) : null
        }
      >
        {quizPending ? (
          <Skeleton active paragraph={{ rows: 4 }} />
        ) : !quiz ? (
          <Empty
            description={
              canManageModule
                ? "Квиз еще не создан. Добавьте тест для проверки знаний."
                : "Тест для этого модуля пока не опубликован"
            }
          >
            {canManageModule ? (
              <Button type="primary" onClick={onOpenQuizDrawer}>
                Создать квиз
              </Button>
            ) : null}
          </Empty>
        ) : (
          <Space direction="vertical" size={18} className="quiz-stack">
            <div>
              <Space wrap>
                <Typography.Title level={4} className="quiz-title">
                  {quiz.title}
                </Typography.Title>
                <Tag color={quiz.is_published ? "green" : "orange"}>
                  {quiz.is_published ? "Опубликован" : "Черновик"}
                </Tag>
                <Tag color={quiz.due_at ? (isDeadlinePassed(quiz.due_at) ? "red" : "geekblue") : "default"}>
                  {formatDeadline(quiz.due_at)}
                </Tag>
                {quiz.has_attempts ? <Tag color="blue">Есть попытки</Tag> : null}
              </Space>
              <Typography.Paragraph className="panel-copy">
                Сейчас квиз работает в формате single-choice: у каждого вопроса один правильный ответ.
              </Typography.Paragraph>
              {canManageModule && quiz.has_attempts ? (
                <Alert
                  type="info"
                  showIcon
                  message="Результаты уже сохранены"
                  description="Теперь можно менять только название и статус публикации. Удаление квиза и изменение вопросов заблокированы, чтобы не сломать историю попыток."
                />
              ) : null}
            </div>

            {canTakeQuiz ? (
              hasCompletedAttempt ? (
                <Card className="quiz-question-card quiz-complete-card">
                  <Space direction="vertical" size={16} className="quiz-complete-stack">
                    <Alert
                      type={correctCount === totalQuestions ? "success" : "info"}
                      showIcon
                      message="Тест завершен"
                      description={`Попытка сохранена. Ваш результат: ${correctCount} из ${totalQuestions}.`}
                    />
                    {quizSubmitResult.is_late ? <Tag color="red">Попытка после дедлайна</Tag> : null}

                    <div className="quiz-summary-grid">
                      <div className="quiz-summary-item">
                        <Typography.Text type="secondary">Правильных ответов</Typography.Text>
                        <Typography.Title level={4}>{correctCount}</Typography.Title>
                      </div>
                      <div className="quiz-summary-item">
                        <Typography.Text type="secondary">Неправильных ответов</Typography.Text>
                        <Typography.Title level={4}>{incorrectCount}</Typography.Title>
                      </div>
                      <div className="quiz-summary-item">
                        <Typography.Text type="secondary">Прогресс попытки</Typography.Text>
                        <Typography.Title level={4}>{attemptPercent}%</Typography.Title>
                      </div>
                    </div>

                    {quizSubmitResult.results.length ? (
                      <div>
                        <Typography.Title level={5}>Разбор ответов</Typography.Title>
                        {quizSubmitResult.results.map((result, index) => (
                          <div key={result.question_id} className="quiz-result-row">
                            <Typography.Text>
                              {index + 1}. {result.is_correct ? "Верно" : "Неверно"}: {result.selected_option}
                            </Typography.Text>
                            {result.explanation ? <div className="quiz-result-explanation">{result.explanation}</div> : null}
                          </div>
                        ))}
                      </div>
                    ) : null}

                    <Space wrap>
                      <Button type="primary" onClick={onRestartAttempt}>
                        Начать новую попытку
                      </Button>
                    </Space>
                  </Space>
                </Card>
              ) : (
                <Form form={quizAnswerForm} layout="vertical" onValuesChange={syncAnswerSnapshot} preserve>
                  <div className="quiz-player-head">
                    <div>
                      <Typography.Title level={5} className="quiz-player-title">
                        Вопрос {currentQuestionIndex + 1} из {totalQuestions}
                      </Typography.Title>
                      <Typography.Text type="secondary">Отвечено на {answeredCount} из {totalQuestions}</Typography.Text>
                    </div>
                    <Progress percent={progressPercent} size="small" className="quiz-player-progress" />
                  </div>

                  {currentQuestion ? (
                    <Card key={currentQuestion.id} className="quiz-question-card quiz-question-card-single">
                      <Typography.Title level={5} className="quiz-question-title">
                        {currentQuestion.content}
                      </Typography.Title>
                      <Form.Item
                        name={["answers", currentQuestion.id]}
                        rules={[{ required: true, message: "Выберите один вариант ответа" }]}
                        preserve
                      >
                        <Radio.Group className="quiz-options-group">
                          <Space direction="vertical" size={10}>
                            {currentQuestion.options.map((option) => (
                              <Radio key={option} value={option}>
                                {option}
                              </Radio>
                            ))}
                          </Space>
                        </Radio.Group>
                      </Form.Item>
                    </Card>
                  ) : null}

                  <div className="quiz-player-nav">
                    <Button icon={<LeftOutlined />} disabled={currentQuestionIndex === 0} onClick={goToPreviousQuestion}>
                      Предыдущий вопрос
                    </Button>

                    {currentQuestionIndex < totalQuestions - 1 ? (
                      <Button type="primary" icon={<RightOutlined />} iconPosition="end" onClick={goToNextQuestion}>
                        Следующий вопрос
                      </Button>
                    ) : (
                      <Button type="primary" loading={submittingQuiz} onClick={requestSubmitQuiz}>
                        Завершить тест
                      </Button>
                    )}
                  </div>
                </Form>
              )
            ) : (
              <List
                dataSource={quiz.questions}
                renderItem={(question, index) => (
                  <List.Item>
                    <div>
                      <Typography.Text strong>
                        {index + 1}. {question.content}
                      </Typography.Text>
                      <div className="quiz-option-preview">Вариантов ответа: {question.options.length}</div>
                    </div>
                  </List.Item>
                )}
              />
            )}

            {attempts.length ? (
              <div>
                <Typography.Title level={5}>Мои попытки</Typography.Title>
                <List
                  dataSource={attempts}
                  renderItem={(attempt) => (
                    <List.Item>
                      <div className="quiz-attempt-row">
                        <Typography.Text>
                          {attempt.score}/{attempt.total_questions}
                        </Typography.Text>
                        {attempt.is_late ? <Tag color="red">Поздно</Tag> : null}
                        <Typography.Text type="secondary">{formatDate(attempt.created_at)}</Typography.Text>
                      </div>
                    </List.Item>
                  )}
                />
              </div>
            ) : null}
          </Space>
        )}
      </Card>

      <Modal
        open={confirmOpen}
        centered
        title="Отправить ответы на тест?"
        okText="Да, отправить"
        cancelText="Вернуться к тесту"
        confirmLoading={submittingQuiz}
        onCancel={() => setConfirmOpen(false)}
        onOk={handleConfirmSubmit}
      >
        <Typography.Paragraph style={{ marginBottom: 0 }}>
          После отправки попытка будет завершена. Затем при необходимости можно начать новую попытку.
        </Typography.Paragraph>
      </Modal>
    </>
  );
}
