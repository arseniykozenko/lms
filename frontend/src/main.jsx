import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { ConfigProvider } from "antd";

import App from "./App";
import { appStarted } from "./models/auth";
import "./styles.css";

const theme = {
  token: {
    colorPrimary: "#0f766e",
    colorInfo: "#0f766e",
    borderRadius: 18,
    fontFamily: "'Trebuchet MS', 'Segoe UI', sans-serif",
  },
};

appStarted();

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <ConfigProvider theme={theme}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </ConfigProvider>
  </React.StrictMode>,
);
