import React, { Suspense } from "react";
import { Spin } from "antd";
import { Navigate, Route, Routes } from "react-router-dom";

import { ProtectedRoute } from "./components/ProtectedRoute";

const AuthPage = React.lazy(() => import("./pages/AuthPage").then((module) => ({ default: module.AuthPage })));
const CourseDetailsPage = React.lazy(() =>
  import("./pages/CourseDetailsPage").then((module) => ({ default: module.CourseDetailsPage })),
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
const MyCoursesPage = React.lazy(() =>
  import("./pages/MyCoursesPage").then((module) => ({ default: module.MyCoursesPage })),
);
const ProfilePage = React.lazy(() =>
  import("./pages/ProfilePage").then((module) => ({ default: module.ProfilePage })),
);

function RouteFallback() {
  return (
    <div className="route-fallback">
      <Spin size="large" />
    </div>
  );
}

export default function App() {
  return (
    <Suspense fallback={<RouteFallback />}>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
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
          path="/courses"
          element={
            <ProtectedRoute>
              <CoursesPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/courses/:courseId"
          element={
            <ProtectedRoute>
              <CourseDetailsPage />
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
      </Routes>
    </Suspense>
  );
}
