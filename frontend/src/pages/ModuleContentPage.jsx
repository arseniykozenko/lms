import React from "react";
import { LeftOutlined, MenuOutlined, RightOutlined } from "@ant-design/icons";
import { Button, Card, Empty, Form, Input, Modal, Select, Skeleton, Space, Tag, Timeline, Typography, message } from "antd";
import { useUnit } from "effector-react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { createReport } from "../api/moderation";
import { transcribeModuleContent } from "../api/modules";
import { ModuleNavigatorDrawer } from "../components/modules/ModuleNavigatorDrawer";
import { getContentTag, getContentTypeLabel, renderContentBody } from "../components/modules/moduleHelpers";
import { PageBreadcrumbs } from "../components/shared/PageBreadcrumbs";
import { myCoursesRefreshRequested } from "../models/auth";
import { $selectedCourseModules, loadCourseModulesFx } from "../models/courses";
import {
  $moduleContents,
  $moduleContentsPending,
  $selectedModule,
  $selectedModulePending,
  loadModuleContentsFx,
  markModuleContentViewedFx,
  modulePageOpened,
  modulePageReset,
} from "../models/modules";

function formatSeconds(value) {
  const total = Math.max(0, Math.floor(Number(value) || 0));
  const minutes = Math.floor(total / 60);
  const seconds = total % 60;
  return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}

export function ModuleContentPage() {
  const { moduleId, contentId } = useParams();
  const navigate = useNavigate();
  const [navOpen, setNavOpen] = React.useState(false);
  const [lastTrackedContentId, setLastTrackedContentId] = React.useState(null);
  const [reportOpen, setReportOpen] = React.useState(false);
  const [reportSubmitting, setReportSubmitting] = React.useState(false);
  const [transcribeSubmitting, setTranscribeSubmitting] = React.useState(false);
  const [transcriptSummary, setTranscriptSummary] = React.useState("");
  const [transcriptTimestamps, setTranscriptTimestamps] = React.useState([]);
  const [transcriptStatus, setTranscriptStatus] = React.useState("");
  const [transcriptError, setTranscriptError] = React.useState("");
  const [reportForm] = Form.useForm();

  const [
    module,
    contents,
    courseModules,
    modulePending,
    contentsPending,
    openModulePage,
    resetModulePage,
    markViewed,
    refreshMyCourses,
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
    markModuleContentViewedFx,
    myCoursesRefreshRequested,
    loadModuleContentsFx,
    loadCourseModulesFx,
  ]);

  React.useEffect(() => {
    if (!moduleId) return undefined;
    openModulePage(moduleId);
    return () => resetModulePage();
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
  const nextModule = currentModuleIndex >= 0 && currentModuleIndex < publishedModules.length - 1
    ? publishedModules[currentModuleIndex + 1]
    : null;

  const currentContent = contents.find((content) => content.id === contentId) || null;
  const currentContentIndex = currentContent ? contents.findIndex((content) => content.id === currentContent.id) : -1;
  const previousContent = currentContentIndex > 0 ? contents[currentContentIndex - 1] : null;
  const nextContent = currentContentIndex >= 0 && currentContentIndex < contents.length - 1
    ? contents[currentContentIndex + 1]
    : null;
  const nextLearningStepHref = nextContent
    ? `/modules/${module?.id}/content/${nextContent.id}`
    : module?.id
      ? `/modules/${module.id}?tab=assignment`
      : null;

  React.useEffect(() => {
    if (!currentContent?.id || lastTrackedContentId === currentContent.id) return;
    markViewed(currentContent.id)
      .then(() => {
        setLastTrackedContentId(currentContent.id);
        refreshMyCourses();
      })
      .catch(() => {});
  }, [currentContent?.id, lastTrackedContentId, markViewed, refreshMyCourses]);

  React.useEffect(() => {
    if (!currentContent) return;
    setTranscriptSummary(currentContent.transcript_summary || "");
    setTranscriptTimestamps(currentContent.transcript_timestamps_json || []);
    setTranscriptStatus(currentContent.transcript_status || "");
    setTranscriptError(currentContent.transcript_error || "");
  }, [currentContent]);

  async function handleTranscribeContent() {
    if (!currentContent?.id) return;
    setTranscribeSubmitting(true);
    setTranscriptError("");
    try {
      const updated = await transcribeModuleContent(currentContent.id);
      setTranscriptSummary(updated.transcript_summary || "");
      setTranscriptTimestamps(updated.transcript_timestamps_json || []);
      setTranscriptStatus(updated.transcript_status || "");
      setTranscriptError(updated.transcript_error || "");
      message.success("Конспект и таймкоды обновлены");
    } catch (error) {
      setTranscriptStatus("failed");
      setTranscriptError(error?.response?.data?.detail || "Не удалось выполнить транскрибацию");
      message.error(error?.response?.data?.detail || "Не удалось выполнить транскрибацию");
    } finally {
      setTranscribeSubmitting(false);
    }
  }

  async function submitContentReport() {
    try {
      const values = await reportForm.validateFields();
      setReportSubmitting(true);
      await createReport({
        target_type: "module_content",
        module_content_id: currentContent.id,
        reason: values.reason,
        category: values.category,
        details: values.details || null,
      });
      message.success("Жалоба отправлена модератору");
      setReportOpen(false);
      reportForm.resetFields();
    } catch (error) {
      message.error(error?.response?.data?.detail || "Не удалось отправить жалобу");
    } finally {
      setReportSubmitting(false);
    }
  }

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
  const isVideoContent = currentContent.content_type === "video";

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
                <Tag color={contentTag.color} icon={contentTag.icon}>{getContentTypeLabel(currentContent.content_type)}</Tag>
                <Tag color="blue">Модуль {module.position}</Tag>
                <Typography.Text type="secondary">Блок {currentContentIndex + 1} из {contents.length}</Typography.Text>
              </Space>

              <Typography.Title level={1} className="immersive-content-title">{currentContent.title}</Typography.Title>
              <Typography.Paragraph className="panel-copy immersive-content-subtitle">{module.title}</Typography.Paragraph>
            </div>

            <Space wrap className="immersive-content-actions">
              <Button icon={<MenuOutlined />} onClick={() => setNavOpen(true)}>Навигация</Button>
              <Button
                danger
                onClick={() => {
                  reportForm.setFieldsValue({
                    category: "misinformation",
                    reason: "Неприемлемый или ошибочный контент",
                    details: "",
                  });
                  setReportOpen(true);
                }}
              >
                Пожаловаться
              </Button>
              <Button><Link to={`/modules/${module.id}`}>К модулю</Link></Button>
              <Button disabled={!previousContent} icon={<LeftOutlined />}>
                {previousContent ? <Link to={`/modules/${module.id}/content/${previousContent.id}`}>Назад</Link> : "Назад"}
              </Button>
              <Button type="primary" disabled={!nextLearningStepHref} icon={<RightOutlined />} iconPosition="end">
                {nextLearningStepHref ? <Link to={nextLearningStepHref}>Далее</Link> : "Далее"}
              </Button>
            </Space>
          </div>

          <div className="immersive-content-stage">{renderContentBody(currentContent)}</div>

          {isVideoContent ? (
            <Card style={{ marginTop: 16 }} bordered={false}>
              <Space direction="vertical" size={14} style={{ width: "100%" }}>
                <Space wrap style={{ justifyContent: "space-between", width: "100%" }}>
                  <Typography.Title level={5} style={{ margin: 0 }}>AI-конспект и таймкоды</Typography.Title>
                  <Button type="primary" loading={transcribeSubmitting} onClick={handleTranscribeContent}>
                    Сгенерировать конспект
                  </Button>
                </Space>
                <Tag color={transcriptStatus === "completed" ? "green" : transcriptStatus === "failed" ? "red" : "blue"}>
                  Статус: {transcriptStatus || "не запускался"}
                </Tag>
                {transcriptError ? <Typography.Text type="danger">{transcriptError}</Typography.Text> : null}

                <Card size="small" title="Краткий конспект">
                  {transcriptSummary ? (
                    <Typography.Paragraph style={{ whiteSpace: "pre-wrap", marginBottom: 0 }}>{transcriptSummary}</Typography.Paragraph>
                  ) : (
                    <Typography.Text type="secondary">Пока нет конспекта. Нажмите «Сгенерировать конспект».</Typography.Text>
                  )}
                </Card>

                <Card size="small" title="Таймкоды по темам">
                  {transcriptTimestamps.length > 0 ? (
                    <Timeline
                      items={transcriptTimestamps.map((item, index) => ({
                        children: (
                          <Space direction="vertical" size={2} key={`${item.start_sec}-${index}`}>
                            <Tag color="cyan" style={{ width: "fit-content" }}>
                              {formatSeconds(item.start_sec)} - {formatSeconds(item.end_sec)}
                            </Tag>
                            <Typography.Text>{item.label}</Typography.Text>
                          </Space>
                        ),
                      }))}
                    />
                  ) : (
                    <Typography.Text type="secondary">Таймкоды появятся после генерации.</Typography.Text>
                  )}
                </Card>
              </Space>
            </Card>
          ) : null}

          <div className="immersive-content-footer">
            <Space wrap>
              {previousModule ? (
                <Button icon={<LeftOutlined />}><Link to={`/modules/${previousModule.id}`}>Предыдущий модуль</Link></Button>
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
          moduleBaseRoute={module?.id ? `/modules/${module.id}` : null}
          activeModuleTab="content"
        />
        <Modal
          title="Пожаловаться на материал"
          open={reportOpen}
          okText="Отправить жалобу"
          cancelText="Отмена"
          confirmLoading={reportSubmitting}
          onOk={submitContentReport}
          onCancel={() => {
            setReportOpen(false);
            reportForm.resetFields();
          }}
        >
          <Form form={reportForm} layout="vertical">
            <Form.Item name="category" label="Категория" rules={[{ required: true, message: "Выберите категорию" }]}>
              <Select
                options={[
                  { value: "misinformation", label: "Ошибочный или вредный контент" },
                  { value: "abuse", label: "Оскорбительный контент" },
                  { value: "copyright", label: "Нарушение авторских прав" },
                  { value: "offtopic", label: "Не по теме" },
                  { value: "other", label: "Другое" },
                ]}
              />
            </Form.Item>
            <Form.Item name="reason" label="Причина" rules={[{ required: true, message: "Укажите причину" }]}>
              <Input />
            </Form.Item>
            <Form.Item name="details" label="Детали (необязательно)">
              <Input.TextArea rows={4} />
            </Form.Item>
          </Form>
        </Modal>
      </div>
    </div>
  );
}
