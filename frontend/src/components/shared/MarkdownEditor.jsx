import React from "react";
import { EyeOutlined, FontSizeOutlined, ItalicOutlined, LinkOutlined, UnorderedListOutlined } from "@ant-design/icons";
import { Button, Input, Segmented, Space, Tooltip, Typography } from "antd";

import { MarkdownContent } from "./MarkdownContent";

const toolbarItems = [
  { key: "heading", icon: <FontSizeOutlined />, label: "Заголовок", before: "## ", after: "" },
  { key: "bold", icon: <strong>B</strong>, label: "Жирный", before: "**", after: "**" },
  { key: "italic", icon: <ItalicOutlined />, label: "Курсив", before: "*", after: "*" },
  { key: "list", icon: <UnorderedListOutlined />, label: "Список", before: "- ", after: "" },
  { key: "link", icon: <LinkOutlined />, label: "Ссылка", before: "[", after: "](https://example.com)" },
];

export function MarkdownEditor({
  value,
  onChange,
  placeholder,
  rows = 10,
  minHeight,
}) {
  const textareaRef = React.useRef(null);
  const [mode, setMode] = React.useState("edit");

  function applySnippet(before, after) {
    const textarea = textareaRef.current?.resizableTextArea?.textArea;
    const currentValue = value || "";

    if (!textarea) {
      onChange?.(`${currentValue}${before}${after}`);
      return;
    }

    const selectionStart = textarea.selectionStart;
    const selectionEnd = textarea.selectionEnd;
    const selectedText = currentValue.slice(selectionStart, selectionEnd);
    const nextValue =
      currentValue.slice(0, selectionStart) +
      before +
      selectedText +
      after +
      currentValue.slice(selectionEnd);

    onChange?.(nextValue);

    requestAnimationFrame(() => {
      textarea.focus();
      const cursorStart = selectionStart + before.length;
      const cursorEnd = cursorStart + selectedText.length;
      textarea.setSelectionRange(cursorStart, cursorEnd || cursorStart);
    });
  }

  return (
    <div className="markdown-editor">
      <div className="markdown-editor-toolbar">
        <Space wrap>
          {toolbarItems.map((item) => (
            <Tooltip key={item.key} title={item.label}>
              <Button type="default" icon={item.icon} onClick={() => applySnippet(item.before, item.after)} />
            </Tooltip>
          ))}
        </Space>

        <Segmented
          size="small"
          options={[
            { label: "Редактор", value: "edit" },
            { label: "Предпросмотр", value: "preview", icon: <EyeOutlined /> },
          ]}
          value={mode}
          onChange={setMode}
        />
      </div>

      {mode === "edit" ? (
        <Input.TextArea
          ref={textareaRef}
          value={value}
          onChange={(event) => onChange?.(event.target.value)}
          placeholder={placeholder}
          rows={rows}
          className="markdown-editor-textarea"
          style={minHeight ? { minHeight } : undefined}
        />
      ) : (
        <div className="markdown-editor-preview" style={minHeight ? { minHeight } : undefined}>
          {value?.trim() ? (
            <MarkdownContent value={value} />
          ) : (
            <Typography.Text type="secondary">Добавьте текст, чтобы увидеть предпросмотр.</Typography.Text>
          )}
        </div>
      )}
    </div>
  );
}
