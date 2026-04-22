import React from "react";
import {
  ArrowRightOutlined,
  LockOutlined,
  MailOutlined,
  SafetyOutlined,
  TeamOutlined,
  UserOutlined,
} from "@ant-design/icons";
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
          full_name: values.full_name?.trim(),
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
            <Typography.Text className="eyebrow">React + FastAPI LMS</Typography.Text>
            <Typography.Title className="auth-title">
              Спокойное и аккуратное пространство для студентов и преподавателей.
            </Typography.Title>
            <Typography.Paragraph className="auth-description">
              Лаконичный вход в вашу LMS: безопасная аутентификация, личные кабинеты по ролям и
              удобная база для дальнейшего развития учебной платформы.
            </Typography.Paragraph>

            <Space direction="vertical" size={18} className="feature-list">
              <Feature
                icon={<SafetyOutlined />}
                title="Надежный вход"
                text="JWT-аутентификация уже подключена к вашему FastAPI API."
              />
              <Feature
                icon={<TeamOutlined />}
                title="Роли и сценарии"
                text="Отдельные акценты в интерфейсе для студентов и преподавателей."
              />
              <Feature
                icon={<ArrowRightOutlined />}
                title="Готово к расширению"
                text="Платформа подготовлена для курсов, модулей и квизов."
              />
            </Space>
          </div>
        </Col>

        <Col xs={24} lg={12}>
          <Card className="auth-card" bordered={false}>
            <Typography.Title level={3}>{isLogin ? "Вход" : "Регистрация"}</Typography.Title>
            <Typography.Paragraph type="secondary">
              {isLogin ? "Войдите в свое учебное пространство." : "Создайте профиль студента или преподавателя."}
            </Typography.Paragraph>

            {error ? <Alert type="error" message={error} showIcon className="auth-alert" /> : null}

            <Form layout="vertical" onFinish={handleFinish} initialValues={{ role: "student" }} size="large">
              {!isLogin ? (
                <Form.Item name="full_name" label="ФИО" rules={[{ required: true, message: "Введите ваше имя" }]}>
                  <Input prefix={<UserOutlined />} placeholder="Арсений Козенко" />
                </Form.Item>
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
