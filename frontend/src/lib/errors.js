export function getErrorStatus(error) {
  return error?.response?.status || null;
}

export function getErrorMessage(error, fallback = "Не удалось выполнить действие") {
  const status = getErrorStatus(error);
  const detail = error?.response?.data?.detail;

  if (typeof detail === "string" && detail.trim()) {
    return detail;
  }

  if (!error?.response) {
    return "Не удалось связаться с сервером. Проверьте подключение и попробуйте еще раз.";
  }

  if (status === 401) {
    return "Сессия истекла или вход не выполнен. Пожалуйста, войдите снова.";
  }

  if (status === 403) {
    return "У вас нет доступа к этому действию или разделу.";
  }

  if (status === 404) {
    return "Запрошенные данные не найдены или уже были удалены.";
  }

  if (status === 409) {
    return "Данные уже были изменены. Обновите страницу и повторите действие.";
  }

  if (status >= 500) {
    return "На сервере произошла ошибка. Попробуйте повторить действие чуть позже.";
  }

  return fallback;
}

export function isNotFoundError(error) {
  return getErrorStatus(error) === 404;
}

export function isForbiddenError(error) {
  return getErrorStatus(error) === 403;
}
