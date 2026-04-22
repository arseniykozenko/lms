import React from "react";
import {
  FileOutlined,
  FilePdfOutlined,
  FileTextOutlined,
  FileWordOutlined,
  InboxOutlined,
  PaperClipOutlined,
} from "@ant-design/icons";
import { Space, Typography } from "antd";

function getFileIcon(fileName = "") {
  const extension = `.${(fileName.split(".").pop() || "").toLowerCase()}`;

  if (extension === ".pdf") return <FilePdfOutlined />;
  if (extension === ".doc" || extension === ".docx") return <FileWordOutlined />;
  if (extension === ".txt") return <FileTextOutlined />;
  if ([".zip", ".rar", ".7z"].includes(extension)) return <InboxOutlined />;
  if (extension === ".pptx") return <PaperClipOutlined />;
  return <FileOutlined />;
}

export function AttachmentList({ attachments = [], emptyText = "Файлы не приложены" }) {
  if (!attachments.length) {
    return <Typography.Text type="secondary">{emptyText}</Typography.Text>;
  }

  return (
    <div className="attachment-list">
      {attachments.map((attachment) => (
        <a
          key={attachment.id || `${attachment.file_url}-${attachment.file_name}`}
          href={attachment.file_url}
          target="_blank"
          rel="noreferrer"
          className="attachment-item"
        >
          <Space size={10}>
            <span className="attachment-icon">{getFileIcon(attachment.file_name)}</span>
            <span className="attachment-name">{attachment.file_name}</span>
          </Space>
        </a>
      ))}
    </div>
  );
}
