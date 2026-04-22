import React from "react";
import { Card, List, Tag, Typography } from "antd";
import { Link } from "react-router-dom";

export function ModuleSidebarNav({ modules, currentModuleId, onNavigate }) {
  return (
    <Card className="panel-card module-sidebar-card" title="Модули курса">
      <List
        dataSource={modules}
        renderItem={(module) => {
          const isActive = module.id === currentModuleId;

          return (
            <List.Item className={`module-nav-item ${isActive ? "module-nav-item-active" : ""}`}>
              {isActive ? (
                <div className="module-nav-content">
                  <div className="module-nav-copy">
                    <Typography.Text type="secondary" className="module-nav-index">
                      {String(module.position).padStart(2, "0")}
                    </Typography.Text>
                    <Typography.Text className="module-nav-title-text">{module.title}</Typography.Text>
                  </div>
                  <div className="module-nav-actions">
                    <Tag color="green">Сейчас</Tag>
                  </div>
                </div>
              ) : (
                <Link className="module-nav-link" to={`/modules/${module.id}`} onClick={onNavigate}>
                  <div className="module-nav-content">
                    <div className="module-nav-copy">
                      <Typography.Text type="secondary" className="module-nav-index">
                        {String(module.position).padStart(2, "0")}
                      </Typography.Text>
                      <Typography.Text className="module-nav-title-text">{module.title}</Typography.Text>
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
    </Card>
  );
}
