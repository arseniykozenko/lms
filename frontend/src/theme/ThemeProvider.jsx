import React from "react";
import { ConfigProvider, theme as antdTheme } from "antd";

const STORAGE_KEY = "lms-theme";

const ThemeModeContext = React.createContext({
  mode: "light",
  toggleMode: () => {},
});

export function ThemeProvider({ children }) {
  const [mode, setMode] = React.useState(() => {
    try {
      return localStorage.getItem(STORAGE_KEY) === "dark" ? "dark" : "light";
    } catch {
      return "light";
    }
  });

  React.useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, mode);
    } catch {
      // ignore
    }
  }, [mode]);

  React.useEffect(() => {
    document.documentElement.setAttribute("data-theme-mode", mode);
  }, [mode]);

  const value = React.useMemo(
    () => ({
      mode,
      toggleMode: () => setMode((current) => (current === "dark" ? "light" : "dark")),
    }),
    [mode],
  );

  const antdConfig = React.useMemo(
    () => ({
      algorithm: mode === "dark" ? antdTheme.darkAlgorithm : antdTheme.defaultAlgorithm,
      token: {
        colorPrimary: mode === "dark" ? "#22a39f" : "#0f766e",
        colorInfo: mode === "dark" ? "#22a39f" : "#0f766e",
        borderRadius: 16,
        fontFamily: "'Trebuchet MS', 'Segoe UI', sans-serif",
        colorBgBase: mode === "dark" ? "#0b1220" : "#f4f7f4",
        colorBgLayout: mode === "dark" ? "#0f172a" : "#f4f7f4",
        colorBgContainer: mode === "dark" ? "#111b2e" : "#ffffff",
        colorTextBase: mode === "dark" ? "#e6edf7" : "#10241f",
        colorText: mode === "dark" ? "#d6dfec" : "#1f2937",
        colorTextSecondary: mode === "dark" ? "#9fb0c8" : "#58746e",
        colorBorder: mode === "dark" ? "#2a3a52" : "#d8e2df",
      },
    }),
    [mode],
  );

  return (
    <ThemeModeContext.Provider value={value}>
      <ConfigProvider theme={antdConfig}>{children}</ConfigProvider>
    </ThemeModeContext.Provider>
  );
}

export function useThemeMode() {
  return React.useContext(ThemeModeContext);
}
