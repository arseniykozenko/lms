import React from "react";
import { Button, Card, Skeleton } from "antd";

import { AppShell } from "../AppShell";

export function ModuleLoadingState() {
  return (
    <AppShell title="Модуль" subtitle="Загружаем материалы модуля.">
      <Card className="panel-card">
        <Skeleton active paragraph={{ rows: 8 }} />
      </Card>
    </AppShell>
  );
}

export function ModuleNotFoundState({ onBack }) {
  return (
    <AppShell title="Модуль не найден" subtitle="Похоже, модуль недоступен или был удален.">
      <Card className="panel-card">
        <Button type="primary" onClick={onBack}>
          Вернуться к курсам
        </Button>
      </Card>
    </AppShell>
  );
}
