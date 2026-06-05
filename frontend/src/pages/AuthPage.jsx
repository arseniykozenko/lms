import React from "react";
import { LockOutlined, MailOutlined, ReadOutlined, SafetyOutlined, ToolOutlined, UserOutlined } from "@ant-design/icons";
import { Alert, Button, Card, Col, Form, Input, Radio, Row, Space, Typography, message } from "antd";
import { useUnit } from "effector-react";
import { useLocation, useNavigate } from "react-router-dom";

import { $authError, $authPending, authErrorReset, signInFx, signUpFx } from "../models/auth";

export function AuthPage({ mode }) {
  const isLogin = mode === "login";
  const navigate = useNavigate();
  const location = useLocation();
  const [loading, error, submitLogin, submitRegister, resetError] = useUnit([
    $authPending,
    $authError,
    signInFx,
    signUpFx,
    authErrorReset,
  ]);

  async function handleFinish(values) {
    resetError();
    const email = values.email?.trim().toLowerCase();
    const password = values.password;

    try {
      if (isLogin) {
        await submitLogin({ email, password });
        message.success("С возвращением");
      } else {
        await submitRegister({
          first_name: values.first_name?.trim(),
          second_name: values.second_name?.trim(),
          email,
          password,
          role: values.role,
        });
        message.success("Аккаунт создан");
      }

      navigate(location.state?.from?.pathname || "/dashboard", { replace: true });
    } catch {
      // error state is already handled in the model
    }
  }

  return (
    <div className="auth-scene">
      <div className="aurora aurora-a" />
      <div className="aurora aurora-b" />

      <Row gutter={[32, 32]} align="middle" className="auth-grid">
        <Col xs={24} lg={12}>
          <div className="auth-copy">
            <Typography.Text className="eyebrow">EdFlow Platform</Typography.Text>
            <Typography.Title className="auth-title">Вход в систему</Typography.Title>
            <Typography.Paragraph className="auth-description">
              Авторизуйтесь, чтобы управлять курсами, заданиями и учебной аналитикой.
            </Typography.Paragraph>

            <Space direction="vertical" size={18} className="feature-list">
              <Feature
                icon={<ReadOutlined />}
                title="Для студента"
                text="Курсы, дедлайны и прогресс."
              />
              <Feature
                icon={<ToolOutlined />}
                title="Для преподавателя"
                text="Управление курсами и проверкой работ."
              />
              <Feature
                icon={<SafetyOutlined />}
                title="Для администратора"
                text="Модерация контента и пользователей."
              />
            </Space>
          </div>
        </Col>

        <Col xs={24} lg={12}>
          <Card className="auth-card" bordered={false}>
            <Typography.Title level={3}>{isLogin ? "Вход" : "Регистрация"}</Typography.Title>
            <Typography.Paragraph type="secondary">
              {isLogin ? "Введите данные аккаунта." : "Создайте аккаунт студента или преподавателя."}
            </Typography.Paragraph>

            {error ? <Alert type="error" message={error} showIcon className="auth-alert" /> : null}

            <Form layout="vertical" onFinish={handleFinish} initialValues={{ role: "student" }} size="large">
              {!isLogin ? (
                <>
                  <Form.Item name="first_name" label="Имя" rules={[{ required: true, message: "Введите имя" }]}>
                    <Input prefix={<UserOutlined />} placeholder="Арсений" />
                  </Form.Item>
                  <Form.Item name="second_name" label="Фамилия" rules={[{ required: true, message: "Введите фамилию" }]}>
                    <Input prefix={<UserOutlined />} placeholder="Козенко" />
                  </Form.Item>
                </>
              ) : null}

              <Form.Item
                name="email"
                label="Электронная почта"
                rules={[
                  { required: true, message: "Введите email" },
                  { type: "email", message: "Введите корректный email" },
                ]}
              >
                <Input prefix={<MailOutlined />} placeholder="name@example.com" autoComplete="email" />
              </Form.Item>

              <Form.Item
                name="password"
                label="Пароль"
                rules={[
                  { required: true, message: "Введите пароль" },
                  { min: 8, message: "Пароль должен быть не короче 8 символов" },
                ]}
              >
                <Input.Password
                  prefix={<LockOutlined />}
                  placeholder="Минимум 8 символов"
                  autoComplete={isLogin ? "current-password" : "new-password"}
                />
              </Form.Item>

              {!isLogin ? (
                <Form.Item name="role" label="Роль">
                  <Radio.Group optionType="button" buttonStyle="solid">
                    <Radio.Button value="student">Студент</Radio.Button>
                    <Radio.Button value="teacher">Преподаватель</Radio.Button>
                  </Radio.Group>
                </Form.Item>
              ) : null}

              <Button type="primary" htmlType="submit" block loading={loading} className="hero-button">
                {isLogin ? "Войти" : "Создать аккаунт"}
              </Button>
            </Form>

            <div className="auth-switch">
              <span>{isLogin ? "Нет аккаунта?" : "Уже есть аккаунт?"}</span>
              <Button type="link" onClick={() => navigate(isLogin ? "/register" : "/login")}>
                {isLogin ? "Зарегистрироваться" : "Войти"}
              </Button>
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  );
}

function Feature({ icon, title, text }) {
  return (
    <div className="feature-item">
      <div className="feature-icon">{icon}</div>
      <div>
        <Typography.Text strong>{title}</Typography.Text>
        <div className="feature-text">{text}</div>
      </div>
    </div>
  );
}
