import React from "react";
import { MailOutlined, UserOutlined } from "@ant-design/icons";
import { Avatar, Card, Typography } from "antd";

export function ProfileHeroCard({ displayPhoto, fullName, email, isTeacher }) {
  return (
    <Card className="profile-hero-card">
      <Avatar size={88} icon={<UserOutlined />} src={displayPhoto} />
      <Typography.Title level={3} className="profile-name">
        {fullName || "Пользователь без имени"}
      </Typography.Title>
      <Typography.Paragraph className="profile-email">
        <MailOutlined /> {email}
      </Typography.Paragraph>
      <div className="profile-role-pill">{isTeacher ? "Профиль преподавателя" : "Профиль студента"}</div>
    </Card>
  );
}
