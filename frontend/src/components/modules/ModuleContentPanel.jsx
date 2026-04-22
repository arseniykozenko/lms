import React from "react";
import { Button, Card, Collapse, Empty, Popconfirm, Space, Typography } from "antd";

import { ContentLabel, renderContentBody } from "./moduleHelpers";

export function ModuleContentPanel({
  contents,
  contentsPending,
  canManageModule,
  deletingContentId,
  onDeleteContent,
  onEditContent,
  onOpenContentDrawer,
}) {
  const contentItems = contents.map((content) => ({
    key: content.id,
    label: <ContentLabel content={content} />,
    extra: canManageModule ? (
      <Space size={4} onClick={(event) => event.stopPropagation()}>
        <Button type="link" size="small" onClick={() => onEditContent(content)}>
          Изменить
        </Button>
        <Popconfirm
          title="Удалить материал?"
          description="Блок контента будет удален из модуля."
          okText="Удалить"
          cancelText="Отмена"
          onConfirm={() => onDeleteContent(content)}
        >
          <Button type="link" size="small" danger loading={deletingContentId === content.id}>
            Удалить
          </Button>
        </Popconfirm>
      </Space>
    ) : null,
    children: <div className="content-collapse-body">{renderContentBody(content)}</div>,
  }));

  return (
    <Card
      className="panel-card"
      title="Контент модуля"
      extra={
        canManageModule ? (
          <Button type="link" onClick={onOpenContentDrawer}>
            Новый блок
          </Button>
        ) : null
      }
    >
      {contents.length === 0 && !contentsPending ? (
        <Empty
          description={
            canManageModule
              ? "Контент еще не добавлен. Начните с первого блока."
              : "Контент модуля пока не опубликован"
          }
        />
      ) : (
        <>
          <Typography.Paragraph className="panel-copy content-accordion-hint">
            Открывайте только тот блок, который нужен сейчас: лекцию, видео, PDF, презентацию PPTX или внешний ресурс.
          </Typography.Paragraph>
          <Collapse
            className="content-collapse"
            items={contentItems}
            defaultActiveKey={contents[0] ? [contents[0].id] : []}
          />
        </>
      )}
    </Card>
  );
}
