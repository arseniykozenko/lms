import React from "react";
import {
  FilePdfOutlined,
  FilePptOutlined,
  FileTextOutlined,
  LinkOutlined,
  VideoCameraOutlined,
} from "@ant-design/icons";
import { Alert, Button, Skeleton, Space, Tag, Typography } from "antd";

const LazyPresentationViewer = React.lazy(() =>
  import("./PresentationViewer").then((module) => ({ default: module.PresentationViewer })),
);

export function getContentTypeLabel(contentType) {
  if (contentType === "text") return "Лекция";
  if (contentType === "video") return "Видео";
  if (contentType === "pdf") return "PDF";
  if (contentType === "presentation") return "Презентация";
  return "Ресурс";
}

export function getContentTag(contentType) {
  if (contentType === "text") return { color: "blue", icon: <FileTextOutlined /> };
  if (contentType === "video") return { color: "red", icon: <VideoCameraOutlined /> };
  if (contentType === "pdf") return { color: "volcano", icon: <FilePdfOutlined /> };
  if (contentType === "presentation") return { color: "purple", icon: <FilePptOutlined /> };
  return { color: "cyan", icon: <LinkOutlined /> };
}

export function formatDate(value) {
  if (!value) return "";
  return new Date(value).toLocaleString("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatDeadline(value) {
  if (!value) return "Без дедлайна";
  return `До ${formatDate(value)}`;
}

export function isDeadlinePassed(value) {
  if (!value) return false;
  return new Date(value).getTime() < Date.now();
}

export function toDateTimeLocalValue(value) {
  if (!value) return "";
  const date = new Date(value);
  const year = String(date.getFullYear());
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  const hours = String(date.getHours()).padStart(2, "0");
  const minutes = String(date.getMinutes()).padStart(2, "0");
  return `${year}-${month}-${day}T${hours}:${minutes}`;
}

export function fromDateTimeLocalValue(value) {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;
  return date.toISOString();
}

export function renderContentBody(content) {
  if (content.content_type === "text") {
    return <Typography.Paragraph className="content-block-text">{content.text_content}</Typography.Paragraph>;
  }

  if (content.content_type === "video") {
    return <video className="content-video-player" controls preload="metadata" src={content.asset_url} />;
  }

  if (content.content_type === "pdf") {
    return (
      <>
        <iframe title={content.title} src={content.asset_url} className="content-pdf-frame" />
        <div className="content-block-actions">
          <Button href={content.asset_url} target="_blank">
            Скачать PDF
          </Button>
        </div>
      </>
    );
  }

  if (content.content_type === "presentation") {
    return (
      <div className="presentation-content-stack">
        <Alert
          type="info"
          showIcon
          message="Презентация открывается прямо внутри модуля"
          description="Файл PPTX можно пролистывать по слайдам без перехода на внешний сервис."
        />
        <React.Suspense fallback={<Skeleton active paragraph={{ rows: 6 }} />}>
          <LazyPresentationViewer url={content.asset_url} title={content.title} />
        </React.Suspense>
        <div className="content-block-actions">
          <Button href={content.asset_url} target="_blank" rel="noreferrer">
            Открыть файл отдельно
          </Button>
          <Button href={content.asset_url} target="_blank" rel="noreferrer">
            Скачать PPTX
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="content-link-card">
      <Alert
        type="info"
        showIcon
        message="Внешние сайты могут запрещать встраивание, поэтому ресурс открывается отдельной страницей."
      />
      <div className="content-block-actions">
        <Button href={content.source_url} target="_blank" rel="noreferrer">
          Открыть ресурс
        </Button>
      </div>
      <Typography.Text type="secondary">{content.source_url}</Typography.Text>
    </div>
  );
}

export function ContentLabel({ content }) {
  const tag = getContentTag(content.content_type);

  return (
    <div className="content-collapse-label">
      <Space wrap>
        <Tag icon={tag.icon} color={tag.color}>
          {getContentTypeLabel(content.content_type)}
        </Tag>
        <Typography.Text strong>{content.title}</Typography.Text>
      </Space>
    </div>
  );
}
