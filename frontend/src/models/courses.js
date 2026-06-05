import { createEffect, createEvent, createStore, sample } from "effector";

import {
  createModule,
  createCourse,
  deleteCourse,
  downloadCourseStudentsCsv,
  enrollInCourse,
  getCourse,
  getCourseAiInsights,
  getCourseModules,
  getStudentCourseAiInsights,
  getCourseStudents,
  getCourses,
  removeCourseStudent,
  reorderCourseModules,
  updateModule,
  updateCourse,
  uploadCourseThumbnail,
} from "../api/courses";
import { myCoursesRefreshRequested } from "./auth";

const AI_STORAGE_KEY = "lms-ai-insights-v2";

function readAiStorage() {
  try {
    const raw = localStorage.getItem(AI_STORAGE_KEY);
    const parsed = raw ? JSON.parse(raw) : null;
    return {
      courseById: parsed?.courseById || {},
      studentById: parsed?.studentById || {},
    };
  } catch {
    return { courseById: {}, studentById: {} };
  }
}

function writeAiStorage(value) {
  localStorage.setItem(AI_STORAGE_KEY, JSON.stringify(value));
}

export const coursesPageOpened = createEvent();
export const courseCreateSubmitted = createEvent();
export const courseEnrollSubmitted = createEvent();
export const coursePublishToggleSubmitted = createEvent();
export const courseStudentsRequested = createEvent();
export const courseStudentRemoved = createEvent();
export const coursePageOpened = createEvent();
export const coursePageReset = createEvent();
export const courseModulesReordered = createEvent();

export const loadCatalogCoursesFx = createEffect(async (filters = {}) => getCourses(filters));
export const loadCourseFx = createEffect(async (courseId) => getCourse(courseId));
export const loadCourseModulesFx = createEffect(async (courseId) => getCourseModules(courseId));
export const createCourseFx = createEffect(async (payload) => createCourse(payload));
export const enrollCourseFx = createEffect(async (courseId) => enrollInCourse(courseId));
export const updateCourseFx = createEffect(async ({ courseId, payload }) => updateCourse(courseId, payload));
export const uploadCourseThumbnailFx = createEffect(async ({ courseId, file }) => uploadCourseThumbnail(courseId, file));
export const deleteCourseFx = createEffect(async (courseId) => deleteCourse(courseId));
export const loadCourseStudentsFx = createEffect(async (courseId) => getCourseStudents(courseId));
export const removeCourseStudentFx = createEffect(async ({ courseId, studentId }) => removeCourseStudent(courseId, studentId));
export const createModuleFx = createEffect(async (payload) => createModule(payload));
export const updateModuleFx = createEffect(async ({ moduleId, payload }) => updateModule(moduleId, payload));
export const reorderCourseModulesFx = createEffect(async ({ courseId, modules }) => reorderCourseModules(courseId, modules));
export const downloadCourseStudentsCsvFx = createEffect(async (courseId) => downloadCourseStudentsCsv(courseId));
export const loadCourseAiInsightsFx = createEffect(async ({ courseId, studentsLimit = 15 }) =>
  getCourseAiInsights(courseId, studentsLimit),
);
export const loadStudentCourseAiInsightsFx = createEffect(async (courseId) => getStudentCourseAiInsights(courseId));

const storedAi = readAiStorage();

export const $catalogCourses = createStore([])
  .on(loadCatalogCoursesFx.doneData, (_, courses) => courses);
export const $selectedCourse = createStore(null)
  .on(loadCourseFx.doneData, (_, course) => course)
  .reset(coursePageReset);
export const $selectedCourseModules = createStore([])
  .on(loadCourseModulesFx.doneData, (_, modules) => modules)
  .reset(coursePageReset);
export const $courseStudents = createStore([])
  .on(loadCourseStudentsFx.doneData, (_, students) => students)
  .reset(coursePageReset);
export const $courseAiInsightsByCourseId = createStore(storedAi.courseById)
  .on(loadCourseAiInsightsFx.done, (state, { params, result }) => ({
    ...state,
    [params.courseId]: result,
  }));
export const $courseAiInsightsErrorByCourseId = createStore({})
  .on(loadCourseAiInsightsFx, (state, { courseId }) => ({ ...state, [courseId]: "" }))
  .on(loadCourseAiInsightsFx.fail, (state, { params, error }) => ({
    ...state,
    [params.courseId]: error?.response?.data?.detail || "Не удалось получить AI-инсайты",
  }));

export const $studentAiInsightsByCourseId = createStore(storedAi.studentById)
  .on(loadStudentCourseAiInsightsFx.done, (state, { params, result }) => ({
    ...state,
    [params]: result,
  }));
export const $studentAiInsightsErrorByCourseId = createStore({})
  .on(loadStudentCourseAiInsightsFx, (state, courseId) => ({ ...state, [courseId]: "" }))
  .on(loadStudentCourseAiInsightsFx.fail, (state, { params, error }) => ({
    ...state,
    [params]: error?.response?.data?.detail || "Не удалось получить AI-рекомендации",
  }));

export const $catalogPending = loadCatalogCoursesFx.pending;
export const $selectedCoursePending = loadCourseFx.pending;
export const $selectedCourseModulesPending = loadCourseModulesFx.pending;
export const $courseCreatePending = createCourseFx.pending;
export const $courseEnrollPending = enrollCourseFx.pending;
export const $courseUpdatePending = updateCourseFx.pending;
export const $courseThumbnailPending = uploadCourseThumbnailFx.pending;
export const $courseDeletePending = deleteCourseFx.pending;
export const $courseStudentsPending = loadCourseStudentsFx.pending;
export const $courseStudentRemovePending = removeCourseStudentFx.pending;
export const $moduleCreatePending = createModuleFx.pending;
export const $moduleUpdatePending = updateModuleFx.pending;
export const $moduleReorderPending = reorderCourseModulesFx.pending;
export const $courseAiInsightsPending = loadCourseAiInsightsFx.pending;
export const $studentAiInsightsPending = loadStudentCourseAiInsightsFx.pending;

$courseAiInsightsByCourseId.watch((courseById) => {
  const current = readAiStorage();
  writeAiStorage({ ...current, courseById });
});

$studentAiInsightsByCourseId.watch((studentById) => {
  const current = readAiStorage();
  writeAiStorage({ ...current, studentById });
});

sample({
  clock: coursesPageOpened,
  fn: () => ({}),
  target: loadCatalogCoursesFx,
});

sample({
  clock: courseCreateSubmitted,
  target: createCourseFx,
});

sample({
  clock: courseEnrollSubmitted,
  target: enrollCourseFx,
});

sample({
  clock: coursePublishToggleSubmitted,
  target: updateCourseFx,
});

sample({
  clock: courseStudentsRequested,
  target: loadCourseStudentsFx,
});

sample({
  clock: coursePageOpened,
  target: loadCourseFx,
});

sample({
  clock: courseStudentRemoved,
  target: removeCourseStudentFx,
});

sample({
  clock: courseModulesReordered,
  target: reorderCourseModulesFx,
});

sample({
  clock: [createCourseFx.done, enrollCourseFx.done, updateCourseFx.done],
  target: loadCatalogCoursesFx,
});

sample({
  clock: [createCourseFx.done, enrollCourseFx.done, updateCourseFx.done],
  target: myCoursesRefreshRequested,
});

sample({
  clock: [uploadCourseThumbnailFx.done, deleteCourseFx.done],
  target: loadCatalogCoursesFx,
});

sample({
  clock: [uploadCourseThumbnailFx.done, deleteCourseFx.done],
  target: myCoursesRefreshRequested,
});

sample({
  clock: [createModuleFx.done, updateModuleFx.done],
  fn: ({ result }) => result.course_id,
  target: loadCourseModulesFx,
});

sample({
  clock: [createModuleFx.done, updateModuleFx.done],
  fn: ({ result }) => result.course_id,
  target: loadCourseFx,
});

sample({
  clock: reorderCourseModulesFx.done,
  fn: ({ params }) => params.courseId,
  target: loadCourseModulesFx,
});

sample({
  clock: removeCourseStudentFx.done,
  fn: ({ params }) => params.courseId,
  target: loadCourseStudentsFx,
});

