import React from "react";
import { LeftOutlined, RightOutlined } from "@ant-design/icons";
import { Alert, Button, Empty, Skeleton, Space, Typography } from "antd";
import { PPTXViewer } from "pptxviewjs";

export function PresentationViewer({ url, title }) {
  const canvasRef = React.useRef(null);
  const stageRef = React.useRef(null);
  const viewerRef = React.useRef(null);
  const [slideCount, setSlideCount] = React.useState(0);
  const [currentSlide, setCurrentSlide] = React.useState(0);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState("");

  const resizeCanvasToStage = React.useCallback(() => {
    const canvas = canvasRef.current;
    const stage = stageRef.current;

    if (!canvas || !stage) {
      return;
    }

    const devicePixelRatio = window.devicePixelRatio || 1;
    const width = Math.max(stage.clientWidth - 20, 320);
    const height = Math.max(stage.clientHeight - 20, Math.round(width * (9 / 16)));

    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;
    canvas.width = Math.round(width * devicePixelRatio);
    canvas.height = Math.round(height * devicePixelRatio);
  }, []);

  const renderCurrentSlide = React.useCallback(async () => {
    const viewer = viewerRef.current;
    const canvas = canvasRef.current;

    if (!viewer || !canvas) {
      return;
    }

    const currentIndex = viewer.getCurrentSlideIndex();
    await viewer.renderSlide(currentIndex, canvas, {
      quality: "high",
    });
    setCurrentSlide(viewer.getCurrentSlideIndex());
  }, []);

  React.useEffect(() => {
    let cancelled = false;

    async function setupViewer() {
      if (!canvasRef.current || !url) {
        return;
      }

      setLoading(true);
      setError("");

      try {
        viewerRef.current?.destroy?.();
        resizeCanvasToStage();
        const viewer = new PPTXViewer({
          canvas: canvasRef.current,
          slideSizeMode: "fit",
          backgroundColor: "#ffffff",
        });

        await viewer.loadFromUrl(url);
        if (cancelled) {
          viewer.destroy();
          return;
        }

        await viewer.render(canvasRef.current, {
          quality: "high",
        });
        if (cancelled) {
          viewer.destroy();
          return;
        }

        viewerRef.current = viewer;
        setSlideCount(viewer.getSlideCount());
        setCurrentSlide(viewer.getCurrentSlideIndex());
      } catch (viewerError) {
        console.error(viewerError);
        if (!cancelled) {
          setError("Не удалось отобразить презентацию внутри модуля");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    setupViewer();

    return () => {
      cancelled = true;
      viewerRef.current?.destroy?.();
      viewerRef.current = null;
    };
  }, [resizeCanvasToStage, url]);

  React.useEffect(() => {
    if (!stageRef.current) {
      return undefined;
    }

    resizeCanvasToStage();

    const observer = new ResizeObserver(() => {
      resizeCanvasToStage();
      renderCurrentSlide().catch(() => {});
    });

    observer.observe(stageRef.current);
    return () => observer.disconnect();
  }, [renderCurrentSlide, resizeCanvasToStage]);

  async function goPrevious() {
    if (!viewerRef.current) return;
    resizeCanvasToStage();
    await viewerRef.current.previousSlide(canvasRef.current);
    await renderCurrentSlide();
    setCurrentSlide(viewerRef.current.getCurrentSlideIndex());
  }

  async function goNext() {
    if (!viewerRef.current) return;
    resizeCanvasToStage();
    await viewerRef.current.nextSlide(canvasRef.current);
    await renderCurrentSlide();
    setCurrentSlide(viewerRef.current.getCurrentSlideIndex());
  }

  return (
    <div className="presentation-viewer-card">
      <div className="presentation-viewer-head">
        <div>
          <Typography.Title level={5} className="presentation-viewer-title">
            {title}
          </Typography.Title>
          <Typography.Text type="secondary">
            {slideCount ? `Слайд ${currentSlide + 1} из ${slideCount}` : "Подготавливаем просмотр"}
          </Typography.Text>
        </div>
        <Space wrap>
          <Button icon={<LeftOutlined />} onClick={goPrevious} disabled={loading || !!error || currentSlide <= 0}>
            Назад
          </Button>
          <Button
            type="primary"
            icon={<RightOutlined />}
            iconPosition="end"
            onClick={goNext}
            disabled={loading || !!error || !slideCount || currentSlide >= slideCount - 1}
          >
            Далее
          </Button>
        </Space>
      </div>

      {loading ? <Skeleton active paragraph={{ rows: 6 }} /> : null}

      {error ? (
        <div className="content-link-card">
          <Alert type="warning" showIcon message={error} description="Можно открыть файл в новой вкладке или скачать его." />
          <div className="content-block-actions">
            <Button href={url} target="_blank" rel="noreferrer">
              Открыть файл
            </Button>
            <Button href={url} target="_blank" rel="noreferrer">
              Скачать PPTX
            </Button>
          </div>
        </div>
      ) : null}

      {!loading && !error && !slideCount ? <Empty description="В презентации не найдено слайдов" /> : null}

      <div ref={stageRef} className={`presentation-viewer-stage ${loading || error ? "presentation-viewer-stage-hidden" : ""}`}>
        <canvas ref={canvasRef} className="presentation-viewer-canvas" />
      </div>
    </div>
  );
}
