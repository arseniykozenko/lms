import React from "react";
import { Button } from "antd";
import { useNavigate } from "react-router-dom";

import { AppStatusPage } from "../components/shared/AppStatusPage";

export function NotFoundPage() {
  const navigate = useNavigate();

  return (
    <AppStatusPage
      status="404"
      title="Страница не найдена"
      subtitle="Похоже, такой страницы нет или ссылка больше неактуальна."
      extra={
        <Button onClick={() => navigate(-1)}>
          Назад
        </Button>
      }
    />
  );
}
