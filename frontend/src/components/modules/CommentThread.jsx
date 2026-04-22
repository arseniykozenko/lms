import React from "react";
import { Button, Popconfirm, Typography } from "antd";

import { formatDate } from "./moduleHelpers";

export function CommentThread({ comment, currentUserId, deletingCommentId, onDelete, onReply, depth = 0 }) {
  const isOwner = currentUserId === comment.user?.id;
  const isDeleted = comment.is_deleted;

  return (
    <div
      className={`comment-thread-card ${depth > 0 ? "comment-thread-card-nested" : ""} ${isDeleted ? "comment-thread-card-deleted" : ""}`}
    >
      <div className="comment-thread-head">
        <div>
          <Typography.Text strong>{isDeleted ? "Удаленный комментарий" : comment.user?.full_name || comment.user?.email}</Typography.Text>
          <div className="comment-thread-meta">{formatDate(comment.created_at)}</div>
          {isDeleted ? <div className="comment-thread-deleted-label">Автор удалил сообщение, но ответы в ветке сохранены</div> : null}
        </div>
        <div>
          {!isDeleted ? (
            <Button type="link" onClick={() => onReply(comment)}>
              Ответить
            </Button>
          ) : null}
          {isOwner && !isDeleted ? (
            <Popconfirm
              title="Удалить комментарий?"
              description="Если у комментария есть ответы, вместо него останется заглушка."
              okText="Удалить"
              cancelText="Отмена"
              onConfirm={() => onDelete(comment)}
            >
              <Button type="link" danger loading={deletingCommentId === comment.id}>
                Удалить
              </Button>
            </Popconfirm>
          ) : null}
        </div>
      </div>
      <Typography.Paragraph className="comment-thread-content" type={isDeleted ? "secondary" : undefined}>
        {comment.content}
      </Typography.Paragraph>

      {comment.replies?.length ? (
        <div className="comment-replies">
          {comment.replies.map((reply) => (
            <CommentThread
              key={reply.id}
              comment={reply}
              currentUserId={currentUserId}
              deletingCommentId={deletingCommentId}
              onDelete={onDelete}
              onReply={onReply}
              depth={depth + 1}
            />
          ))}
        </div>
      ) : null}
    </div>
  );
}
