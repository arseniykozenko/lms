import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes("node_modules")) {
            return undefined;
          }

          if (id.includes("pptxviewjs") || id.includes("jszip") || id.includes("chart.js")) {
            return "presentation-vendor";
          }

          if (
            id.includes("antd") ||
            id.includes("@ant-design") ||
            id.includes("\\rc-") ||
            id.includes("/rc-") ||
            id.includes("@rc-component") ||
            id.includes("dayjs")
          ) {
            return "antd-vendor";
          }

          if (id.includes("react-router")) {
            return "router-vendor";
          }

          if (id.includes("effector")) {
            return "effector-vendor";
          }

          if (id.includes("react") || id.includes("scheduler")) {
            return "react-vendor";
          }

          if (id.includes("axios")) {
            return "http-vendor";
          }

          return "vendor";
        },
      },
    },
  },
});
