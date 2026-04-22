import React from "react";
import { LeftOutlined, MenuOutlined, RightOutlined } from "@ant-design/icons";
import { Button, Empty, Skeleton, Space, Tag, Typography } from "antd";
import { useUnit } from "effector-react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { ModuleNavigatorDrawer } from "../components/modules/ModuleNavigatorDrawer";
import { getContentTag, getContentTypeLabel, renderContentBody } from "../components/modules/moduleHelpers";
import { PageBreadcrumbs } from "../components/shared/PageBreadcrumbs";
import { $selectedCourseModules, loadCourseModulesFx } from "../models/courses";
import {
  $moduleContents,
  $moduleContentsPending,
  $selectedModule,
  $selectedModulePending,
  loadModuleContentsFx,
  modulePageOpened,
  modulePageReset,
} from "../models/modules";

export function ModuleContentPage() {
  const { moduleId, contentId } = useParams();
  const navigate = useNavigate();
  const [navOpen, setNavOpen] = React.useState(false);
  const [
    module,
    contents,
    courseModules,
    modulePending,
    contentsPending,
    openModulePage,
    resetModulePage,
    loadContents,
    loadCourseModules,
  ] = useUnit([
    $selectedModule,
    $moduleContents,
    $selectedCourseModules,
    $selectedModulePending,
    $moduleContentsPending,
    modulePageOpened,
    modulePageReset,
    loadModuleContentsFx,
    loadCourseModulesFx,
  ]);

  React.useEffect(() => {
    if (!moduleId) return undefined;

    openModulePage(moduleId);

    return () => {
      resetModulePage();
    };
  }, [moduleId, openModulePage, resetModulePage]);

  React.useEffect(() => {
    if (!module?.course_id) return;
    loadCourseModules(module.course_id).catch(() => {});
  }, [module?.course_id, loadCourseModules]);

  React.useEffect(() => {
    if (!moduleId) return;
    loadContents(moduleId).catch(() => {});
  }, [moduleId, loadContents]);

  const publishedModules = courseModules.filter((courseModule) => courseModule.is_published);
  const currentModuleIndex = publishedModules.findIndex((courseModule) => courseModule.id === module?.id);
  const previousModule = currentModuleIndex > 0 ? publishedModules[currentModuleIndex - 1] : null;
  const nextModule =
    currentModuleIndex >= 0 && currentModuleIndex < publishedModules.length - 1
      ? publishedModules[currentModuleIndex + 1]
      : null;

  const currentContent = contents.find((content) => content.id === contentId) || null;
  const currentContentIndex = currentContent ? contents.findIndex((content) => content.id === currentContent.id) : -1;
  const previousContent = currentContentIndex > 0 ? contents[currentContentIndex - 1] : null;
  const nextContent =
    currentContentIndex >= 0 && currentContentIndex < contents.length - 1 ? contents[currentContentIndex + 1] : null;

  if ((modulePending && !module) || (contentsPending && !contents.length)) {
    return (
      <div className="immersive-page-shell">
        <div className="immersive-page-inner">
          <div className="panel-card immersive-loading-card">
            <Skeleton active paragraph={{ rows: 10 }} />
          </div>
        </div>
      </div>
    );
  }

  if (!module || !currentContent) {
    return (
      <div className="immersive-page-shell">
        <div className="immersive-page-inner">
          <div className="panel-card immersive-loading-card">
            <Empty description="Материал не найден" />
            <Space>
              <Button type="primary" onClick={() => navigate(moduleId ? `/modules/${moduleId}` : "/courses")}>
                Вернуться к модулю
              </Button>
              <Button onClick={() => navigate("/courses")}>К курсам</Button>
            </Space>
          </div>
        </div>
      </div>
    );
  }

  const contentTag = getContentTag(currentContent.content_type);

  return (
    <div className="immersive-page-shell">
      <div className="immersive-page-inner">
        <PageBreadcrumbs
          items={[
            { label: "Главная", href: "/dashboard" },
            { label: "Каталог курсов", href: "/courses" },
            { label: module.course_title || "Курс", href: `/courses/${module.course_id}` },
            { label: module.title, href: `/modules/${module.id}` },
            { label: currentContent.title },
          ]}
        />

        <div className="immersive-content-card panel-card">
          <div className="immersive-content-head">
            <div className="immersive-content-copy">
              <Space wrap>
                <Tag color={contentTag.color} icon={contentTag.icon}>
                  {getContentTypeLabel(currentContent.content_type)}
                </Tag>
                <Tag color="blue">Модуль {module.position}</Tag>
                <Typography.Text type="secondary">
                  Блок {currentContentIndex + 1} из {contents.length}
                </Typography.Text>
              </Space>

              <Typography.Title level={1} className="immersive-content-title">
                {currentContent.title}
              </Typography.Title>

              <Typography.Paragraph className="panel-copy immersive-content-subtitle">
                {module.title}
              </Typography.Paragraph>
            </div>

            <Space wrap className="immersive-content-actions">
              <Button icon={<MenuOutlined />} onClick={() => setNavOpen(true)}>
                Навигация
              </Button>
              <Button>
                <Link to={`/modules/${module.id}`}>К модулю</Link>
              </Button>
              <Button disabled={!previousContent} icon={<LeftOutlined />}>
                {previousContent ? <Link to={`/modules/${module.id}/content/${previousContent.id}`}>Назад</Link> : "Назад"}
              </Button>
              <Button type="primary" disabled={!nextContent} icon={<RightOutlined />} iconPosition="end">
                {nextContent ? <Link to={`/modules/${module.id}/content/${nextContent.id}`}>Далее</Link> : "Далее"}
              </Button>
            </Space>
          </div>

          <div className="immersive-content-stage">{renderContentBody(currentContent)}</div>

          <div className="immersive-content-footer">
            <Space wrap>
              {previousModule ? (
                <Button icon={<LeftOutlined />}>
                  <Link to={`/modules/${previousModule.id}`}>Предыдущий модуль</Link>
                </Button>
              ) : null}
              {nextModule ? (
                <Button type="primary" icon={<RightOutlined />} iconPosition="end">
                  <Link to={`/modules/${nextModule.id}`}>Следующий модуль</Link>
                </Button>
              ) : null}
            </Space>
          </div>
        </div>

        <ModuleNavigatorDrawer
          open={navOpen}
          onClose={() => setNavOpen(false)}
          modules={publishedModules}
          currentModuleId={module?.id}
          contents={contents}
          currentContentId={currentContent?.id}
        />
      </div>
    </div>
  );
}
