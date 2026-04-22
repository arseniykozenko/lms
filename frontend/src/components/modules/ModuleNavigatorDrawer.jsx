import React from "react";
import { Card, Drawer, List, Tag, Typography } from "antd";
import { Link } from "react-router-dom";

import { getContentTag, getContentTypeLabel } from "./moduleHelpers";
import { ModuleSidebarNav } from "./ModuleSidebarNav";

export function ModuleNavigatorDrawer({
  open,
  onClose,
  modules,
  currentModuleId,
  contents = [],
  currentContentId = null,
}) {
  const currentModule = modules.find((module) => module.id === currentModuleId) || null;

  return (
    <Drawer
      title="Навигация по курсу"
      placement="right"
      open={open}
      onClose={onClose}
      width={392}
      className="module-nav-drawer"
    >
      <div className="module-nav-drawer-stack">
        <ModuleSidebarNav modules={modules} currentModuleId={currentModuleId} onNavigate={onClose} />

        <Card
          className="panel-card module-sidebar-card"
          title={currentModule ? `Материалы: ${currentModule.title}` : "Материалы модуля"}
        >
          {contents.length ? (
            <List
              dataSource={contents}
              renderItem={(content, index) => {
                const isActive = content.id === currentContentId;
                const tag = getContentTag(content.content_type);

                return (
                  <List.Item className={`module-nav-item ${isActive ? "module-nav-item-active" : ""}`}>
                    {isActive ? (
                      <div className="module-nav-content">
                        <div className="module-nav-copy">
                          <Typography.Text type="secondary" className="module-nav-index">
                            {String(index + 1).padStart(2, "0")}
                          </Typography.Text>
                          <div className="module-nav-meta-copy">
                            <Typography.Text className="module-nav-title-text">{content.title}</Typography.Text>
                            <Tag color={tag.color} icon={tag.icon} className="module-nav-kind-tag">
                              {getContentTypeLabel(content.content_type)}
                            </Tag>
                          </div>
                        </div>
                        <div className="module-nav-actions">
                          <Tag color="gold">Сейчас</Tag>
                        </div>
                      </div>
                    ) : (
                      <Link className="module-nav-link" to={`/modules/${currentModuleId}/content/${content.id}`} onClick={onClose}>
                        <div className="module-nav-content">
                          <div className="module-nav-copy">
                            <Typography.Text type="secondary" className="module-nav-index">
                              {String(index + 1).padStart(2, "0")}
                            </Typography.Text>
                            <div className="module-nav-meta-copy">
                              <Typography.Text className="module-nav-title-text">{content.title}</Typography.Text>
                              <Tag color={tag.color} icon={tag.icon} className="module-nav-kind-tag">
                                {getContentTypeLabel(content.content_type)}
                              </Tag>
                            </div>
                          </div>
                          <div className="module-nav-actions">
                            <Typography.Text className="module-nav-open">Открыть</Typography.Text>
                          </div>
                        </div>
                      </Link>
                    )}
                  </List.Item>
                );
              }}
            />
          ) : (
            <div className="module-nav-empty">
              <Typography.Text type="secondary">Материалы этого модуля пока не опубликованы.</Typography.Text>
            </div>
          )}
        </Card>
      </div>
    </Drawer>
  );
}
