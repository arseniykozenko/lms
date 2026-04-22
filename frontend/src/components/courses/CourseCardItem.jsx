import React from "react";
import { BookOutlined } from "@ant-design/icons";
import { Card, Space, Typography } from "antd";

export function CourseCardItem({ course, tags, footer, loading = false }) {
  return (
    <Card
      className="panel-card course-card"
      loading={loading}
      cover={
        <div
          className="course-card-cover"
          style={
            course.thumbnail_url
              ? {
                  backgroundImage: `linear-gradient(rgba(16,36,31,0.14), rgba(16,36,31,0.14)), url(${course.thumbnail_url})`,
                }
              : undefined
          }
        >
          {!course.thumbnail_url ? <BookOutlined className="course-card-cover-icon" /> : null}
        </div>
      }
    >
      <Space className="course-card-tags" wrap>
        {tags}
      </Space>
      <Typography.Title level={4} className="course-card-title">
        {course.title}
      </Typography.Title>
      <Typography.Paragraph className="course-card-description">
        {course.description}
      </Typography.Paragraph>
      <div className="course-card-footer">{footer}</div>
    </Card>
  );
}
