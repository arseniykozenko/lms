import { combine, createEffect, createEvent, createStore, sample } from "effector";

import {
  getCurrentUser,
  getMyCourses,
  loginUser,
  registerUser,
  updateProfile,
  uploadProfilePhoto,
} from "../api/auth";
import { setAuthToken } from "../api/client";

const STORAGE_KEY = "lms-auth";

function readStorage() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function writeStorage(value) {
  if (!value) {
    localStorage.removeItem(STORAGE_KEY);
    return;
  }

  localStorage.setItem(STORAGE_KEY, JSON.stringify(value));
}

export const appStarted = createEvent();
export const signInSubmitted = createEvent();
export const signUpSubmitted = createEvent();
export const signOutClicked = createEvent();
export const profileSaveSubmitted = createEvent();
export const profilePhotoSaveSubmitted = createEvent();
export const myCoursesRefreshRequested = createEvent();
export const authErrorReset = createEvent();

export const loadMyCoursesFx = createEffect(async () => getMyCourses());

export const restoreSessionFx = createEffect(async () => {
  const stored = readStorage();

  if (!stored?.token) {
    setAuthToken(null);
    return { token: null, user: null, courses: [], ready: true };
  }

  setAuthToken(stored.token);

  try {
    const [user, courses] = await Promise.all([getCurrentUser(), loadMyCoursesFx()]);
    writeStorage({ token: stored.token, user });
    return { token: stored.token, user, courses, ready: true };
  } catch {
    setAuthToken(null);
    writeStorage(null);
    return { token: null, user: null, courses: [], ready: true };
  }
});

export const signInFx = createEffect(async (payload) => {
  const response = await loginUser(payload);
  setAuthToken(response.access_token);
  const courses = await loadMyCoursesFx().catch(() => []);
  writeStorage({ token: response.access_token, user: response.user });

  return {
    token: response.access_token,
    user: response.user,
    courses,
  };
});

export const signUpFx = createEffect(async (payload) => {
  const response = await registerUser(payload);
  setAuthToken(response.access_token);
  const courses = await loadMyCoursesFx().catch(() => []);
  writeStorage({ token: response.access_token, user: response.user });

  return {
    token: response.access_token,
    user: response.user,
    courses,
  };
});

export const saveProfileFx = createEffect(async (payload) => {
  const user = await updateProfile(payload);
  const token = $token.getState();
  writeStorage({ token, user });
  return user;
});

export const saveProfilePhotoFx = createEffect(async (file) => {
  const user = await uploadProfilePhoto(file);
  const token = $token.getState();
  writeStorage({ token, user });
  return user;
});

export const $token = createStore(null);
export const $user = createStore(null);
export const $courses = createStore([]);
export const $sessionReady = createStore(false);
export const $authError = createStore("");

export const $authPending = combine(
  restoreSessionFx.pending,
  signInFx.pending,
  signUpFx.pending,
  (restoring, signingIn, signingUp) => restoring || signingIn || signingUp,
);

export const $profilePending = saveProfileFx.pending;
export const $photoPending = saveProfilePhotoFx.pending;
export const $isAuthenticated = combine($token, $user, (token, user) => Boolean(token && user));

sample({
  clock: appStarted,
  target: restoreSessionFx,
});

sample({
  clock: signInSubmitted,
  target: signInFx,
});

sample({
  clock: signUpSubmitted,
  target: signUpFx,
});

sample({
  clock: profileSaveSubmitted,
  target: saveProfileFx,
});

sample({
  clock: profilePhotoSaveSubmitted,
  target: saveProfilePhotoFx,
});

sample({
  clock: myCoursesRefreshRequested,
  target: loadMyCoursesFx,
});

$token
  .on(restoreSessionFx.doneData, (_, payload) => payload.token)
  .on(signInFx.doneData, (_, payload) => payload.token)
  .on(signUpFx.doneData, (_, payload) => payload.token)
  .reset(signOutClicked);

$user
  .on(restoreSessionFx.doneData, (_, payload) => payload.user)
  .on(signInFx.doneData, (_, payload) => payload.user)
  .on(signUpFx.doneData, (_, payload) => payload.user)
  .on(saveProfileFx.doneData, (_, user) => user)
  .on(saveProfilePhotoFx.doneData, (_, user) => user)
  .reset(signOutClicked);

$courses
  .on(restoreSessionFx.doneData, (_, payload) => payload.courses)
  .on(signInFx.doneData, (_, payload) => payload.courses)
  .on(signUpFx.doneData, (_, payload) => payload.courses)
  .on(loadMyCoursesFx.doneData, (_, payload) => payload)
  .reset(signOutClicked);

$sessionReady
  .on(restoreSessionFx.done, () => true)
  .on(signInFx.done, () => true)
  .on(signUpFx.done, () => true)
  .on(signOutClicked, () => true);

$authError
  .on(signInFx.failData, (_, error) => error?.response?.data?.detail || "Не удалось выполнить вход")
  .on(signUpFx.failData, (_, error) => error?.response?.data?.detail || "Не удалось выполнить регистрацию")
  .reset(authErrorReset, signInFx.done, signUpFx.done, signOutClicked);

signOutClicked.watch(() => {
  setAuthToken(null);
  writeStorage(null);
});

restoreSessionFx.doneData.watch(({ token }) => {
  if (!token) {
    setAuthToken(null);
  }
});
