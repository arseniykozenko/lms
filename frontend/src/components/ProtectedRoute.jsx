import React from "react";
import { useUnit } from "effector-react";
import { Navigate, useLocation } from "react-router-dom";
import { Spin } from "antd";

import { $authPending, $isAuthenticated, $sessionReady } from "../models/auth";

export function ProtectedRoute({ children }) {
  const location = useLocation();
  const [isAuthenticated, sessionReady, authPending] = useUnit([$isAuthenticated, $sessionReady, $authPending]);

  if (!sessionReady || authPending) {
    return (
      <div className="screen-shell centered-shell">
        <Spin size="large" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return children;
}
