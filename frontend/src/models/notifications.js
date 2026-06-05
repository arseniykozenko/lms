import { createEffect, createEvent, createStore, sample } from "effector";

import { signInFx, signOutClicked, signUpFx } from "./auth";
import {
  deleteNotification,
  deleteReadNotifications,
  getMyNotifications,
  markAllNotificationsRead,
  markNotificationRead,
} from "../api/notifications";

export const notificationsRefreshRequested = createEvent();

export const loadNotificationsFx = createEffect(async () => getMyNotifications());
export const markNotificationReadFx = createEffect(async (notificationId) => markNotificationRead(notificationId));
export const markAllNotificationsReadFx = createEffect(async () => {
  await markAllNotificationsRead();
});
export const deleteNotificationFx = createEffect(async (notificationId) => {
  await deleteNotification(notificationId);
});
export const deleteReadNotificationsFx = createEffect(async () => {
  await deleteReadNotifications();
});

export const $notifications = createStore([])
  .on(loadNotificationsFx.doneData, (_, payload) => payload.items || [])
  .reset(signOutClicked);

export const $notificationsUnreadCount = createStore(0)
  .on(loadNotificationsFx.doneData, (_, payload) => payload.unread_count || 0)
  .reset(signOutClicked);

sample({
  clock: [signInFx.done, signUpFx.done, notificationsRefreshRequested],
  target: loadNotificationsFx,
});

sample({
  clock: [
    markNotificationReadFx.done,
    markAllNotificationsReadFx.done,
    deleteNotificationFx.done,
    deleteReadNotificationsFx.done,
  ],
  target: loadNotificationsFx,
});
