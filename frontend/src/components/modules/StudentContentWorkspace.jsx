import React from "react";
import { Button, Card, Empty, List, Space, Tag, Typography } from "antd";
import { Link } from "react-router-dom";

import { getContentTypeLabel, getContentTag } from "./moduleHelpers";

export function StudentContentWorkspace({ moduleId, contents }) {
  if (!contents.length) {
    return (
      <Card className="panel-card student-content-shell-card">
        <Empty description="Материалы модуля пока не опубликованы" />
      </Card>
    );
  }

  return (
    <Card className="panel-card student-content-shell-card">
      <div className="student-content-shell-head">
        <div>
          <Typography.Title level={4} className="student-content-shell-title">
            Материалы модуля
          </Typography.Title>
          <Typography.Paragraph className="panel-copy student-content-shell-copy">
            Каждый материал открывается как отдельная учебная страница с собственным адресом и навигацией.
          </Typography.Paragraph>
        </div>
      </div>

      <List
        className="student-content-list"
        dataSource={contents}
        renderItem={(content, index) => {
          const tag = getContentTag(content.content_type);
          return (
            <List.Item className="student-content-list-item">
              <div className="student-content-list-row">
                <div className="student-content-list-copy">
                  <Space wrap>
                    <Tag color={tag.color} icon={tag.icon}>
                      {getContentTypeLabel(content.content_type)}
                    </Tag>
                    <Typography.Text type="secondary">Блок {index + 1}</Typography.Text>
                  </Space>
                  <Typography.Title level={5} className="student-content-list-title">
                    {content.title}
                  </Typography.Title>
                </div>
                <Button type="primary">
                  <Link to={`/modules/${moduleId}/content/${content.id}`}>Открыть материал</Link>
                </Button>
              </div>
            </List.Item>
          );
        }}
      />
    </Card>
  );
}
