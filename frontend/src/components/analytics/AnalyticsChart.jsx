import React from "react";
import Chart from "chart.js/auto";
import { useThemeMode } from "../../theme/ThemeProvider";

export function AnalyticsChart({ type, data, options, height = 260 }) {
  const canvasRef = React.useRef(null);
  const chartRef = React.useRef(null);
  const { mode } = useThemeMode();
  const isDark = mode === "dark";

  React.useEffect(() => {
    if (!canvasRef.current) return undefined;

    if (chartRef.current) {
      chartRef.current.destroy();
    }

    const isCircular = type === "doughnut" || type === "pie" || type === "polarArea";

    chartRef.current = new Chart(canvasRef.current, {
      type,
      data,
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: {
          duration: 500,
          easing: "easeOutQuart",
        },
        interaction: isCircular
          ? {
              mode: "nearest",
              intersect: true,
            }
          : {
              mode: "index",
              intersect: false,
            },
        plugins: {
          legend: {
            labels: {
              color: isDark ? "#e2e8f0" : "#334155",
              boxWidth: 10,
              usePointStyle: true,
            },
          },
          tooltip: {
            cornerRadius: 12,
            backgroundColor: "rgba(15, 23, 42, 0.92)",
            titleColor: "#f8fafc",
            bodyColor: "#e2e8f0",
            padding: 12,
          },
        },
        ...options,
      },
    });

    return () => {
      if (chartRef.current) {
        chartRef.current.destroy();
        chartRef.current = null;
      }
    };
  }, [data, isDark, options, type]);

  return (
    <div style={{ height }} className="analytics-chart-frame">
      <canvas ref={canvasRef} />
    </div>
  );
}
