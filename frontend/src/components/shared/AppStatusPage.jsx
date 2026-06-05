import React from "react";
import { Button, Card, Result, Space } from "antd";
import { useNavigate } from "react-router-dom";

import { AppShell } from "../AppShell";

export function AppStatusPage({
  status = "info",
  title,
  subtitle,
  extra,
  showHome = true,
  homeLabel = "На главную",
}) {
  const navigate = useNavigate();

  return (
    <AppShell title={title} subtitle={subtitle}>
      <Card className="panel-card">
        <Result
          status={status}
          title={title}
          subTitle={subtitle}
          extra={
            <Space wrap>
              {extra}
              {showHome ? (
                <Button type="primary" onClick={() => navigate("/dashboard")}>
                  {homeLabel}
                </Button>
              ) : null}
            </Space>
          }
        />
      </Card>
    </AppShell>
  );
}
