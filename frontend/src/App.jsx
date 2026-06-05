import React, { Suspense } from "react";
import { Spin } from "antd";
import { useUnit } from "effector-react";
import { Navigate, Route, Routes } from "react-router-dom";

import { AppErrorBoundary } from "./components/AppErrorBoundary";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { $isAuthenticated, $sessionReady } from "./models/auth";

const AuthPage = React.lazy(() => import("./pages/AuthPage").then((module) => ({ default: module.AuthPage })));
const CourseDetailsPage = React.lazy(() =>
  import("./pages/CourseDetailsPage").then((module) => ({ default: module.CourseDetailsPage })),
);
const ChatPage = React.lazy(() => import("./pages/ChatPage").then((module) => ({ default: module.ChatPage })));
const CourseProgressPage = React.lazy(() =>
  import("./pages/CourseProgressPage").then((module) => ({ default: module.CourseProgressPage })),
);
const CoursesPage = React.lazy(() =>
  import("./pages/CoursesPage").then((module) => ({ default: module.CoursesPage })),
);
const DashboardPage = React.lazy(() =>
  import("./pages/DashboardPage").then((module) => ({ default: module.DashboardPage })),
);
const ModuleDetailsPage = React.lazy(() =>
  import("./pages/ModuleDetailsPage").then((module) => ({ default: module.ModuleDetailsPage })),
);
const ModuleContentPage = React.lazy(() =>
  import("./pages/ModuleContentPage").then((module) => ({ default: module.ModuleContentPage })),
);
const NotFoundPage = React.lazy(() =>
  import("./pages/NotFoundPage").then((module) => ({ default: module.NotFoundPage })),
);
const MyCoursesPage = React.lazy(() =>
  import("./pages/MyCoursesPage").then((module) => ({ default: module.MyCoursesPage })),
);
const ProfilePage = React.lazy(() =>
  import("./pages/ProfilePage").then((module) => ({ default: module.ProfilePage })),
);
const ModerationPage = React.lazy(() =>
  import("./pages/ModerationPage").then((module) => ({ default: module.ModerationPage })),
);

function RouteFallback() {
  return (
    <div className="route-fallback">
      <Spin size="large" />
    </div>
  );
}

export default function App() {
  const [isAuthenticated, sessionReady] = useUnit([$isAuthenticated, $sessionReady]);

  if (!sessionReady) {
    return <RouteFallback />;
  }

  return (
    <AppErrorBoundary>
      <Suspense fallback={<RouteFallback />}>
        <Routes>
          <Route path="/" element={<Navigate to={isAuthenticated ? "/dashboard" : "/courses"} replace />} />
          <Route path="/login" element={<AuthPage mode="login" />} />
          <Route path="/register" element={<AuthPage mode="register" />} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/chat"
            element={
              <ProtectedRoute>
                <ChatPage />
              </ProtectedRoute>
            }
          />
          <Route path="/courses" element={<CoursesPage />} />
          <Route
            path="/courses/:courseId"
            element={
              <ProtectedRoute>
                <CourseDetailsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/courses/:courseId/progress"
            element={
              <ProtectedRoute>
                <CourseProgressPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/my-courses"
            element={
              <ProtectedRoute>
                <MyCoursesPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/profile"
            element={
              <ProtectedRoute>
                <ProfilePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/moderation"
            element={
              <ProtectedRoute>
                <ModerationPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/modules/:moduleId"
            element={
              <ProtectedRoute>
                <ModuleDetailsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/modules/:moduleId/content/:contentId"
            element={
              <ProtectedRoute>
                <ModuleContentPage />
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </Suspense>
    </AppErrorBoundary>
  );
}
