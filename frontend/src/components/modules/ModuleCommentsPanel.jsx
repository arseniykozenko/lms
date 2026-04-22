import React from "react";
import { CommentOutlined } from "@ant-design/icons";
import { Alert, Button, Card, Divider, Empty, Form, Input, List, Space, Typography } from "antd";

import { CommentThread } from "./CommentThread";

export function ModuleCommentsPanel({
  comments,
  commentsPending,
  commentForm,
  creatingComment,
  deletingCommentId,
  currentUserId,
  replyTarget,
  onCancelReply,
  onDelete,
  onSubmit,
  onReply,
}) {
  return (
    <Card
      className="panel-card"
      title={
        <Space>
          <CommentOutlined />
          <span>Комментарии</span>
        </Space>
      }
    >
      <Typography.Paragraph className="panel-copy">
        Можно обсудить материал, задать вопрос по лекции или ответить на конкретный комментарий.
      </Typography.Paragraph>

      {replyTarget ? (
        <Alert
          className="comment-reply-alert"
          type="info"
          showIcon
          message={`Ответ на комментарий: ${replyTarget.user?.full_name || replyTarget.user?.email}`}
          description={replyTarget.content}
          action={
            <Button size="small" onClick={onCancelReply}>
              Отменить
            </Button>
          }
        />
      ) : null}

      <Form form={commentForm} layout="vertical" onFinish={onSubmit}>
        <Form.Item
          name="content"
          label={replyTarget ? "Ваш ответ" : "Новый комментарий"}
          rules={[{ required: true, message: "Введите текст комментария" }]}
        >
          <Input.TextArea
            rows={4}
            placeholder={
              replyTarget
                ? "Напишите ответ по теме обсуждения"
                : "Напишите вопрос, замечание или комментарий к модулю"
            }
          />
        </Form.Item>
        <Button type="primary" htmlType="submit" loading={creatingComment}>
          {replyTarget ? "Отправить ответ" : "Отправить комментарий"}
        </Button>
      </Form>

      <Divider />

      {comments.length === 0 && !commentsPending ? (
        <Empty description="Пока комментариев нет. Начните обсуждение первым." />
      ) : (
        <List
          itemLayout="vertical"
          dataSource={comments}
          renderItem={(comment) => (
            <List.Item key={comment.id} className="comment-thread-item">
              <CommentThread
                comment={comment}
                currentUserId={currentUserId}
                deletingCommentId={deletingCommentId}
                onDelete={onDelete}
                onReply={onReply}
              />
            </List.Item>
          )}
        />
      )}
    </Card>
  );
}
