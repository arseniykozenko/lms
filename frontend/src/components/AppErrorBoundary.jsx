import React from "react";
import { Button } from "antd";

import { AppStatusPage } from "./shared/AppStatusPage";

export class AppErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error) {
    console.error("Unhandled UI error", error);
  }

  render() {
    if (this.state.hasError) {
      return (
        <AppStatusPage
          status="500"
          title="Что-то пошло не так"
          subtitle="Интерфейс столкнулся с неожиданной ошибкой. Можно обновить страницу или вернуться на главную."
          extra={
            <Button onClick={() => window.location.reload()}>
              Обновить страницу
            </Button>
          }
        />
      );
    }

    return this.props.children;
  }
}
