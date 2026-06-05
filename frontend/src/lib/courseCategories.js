export const POPULAR_COURSE_CATEGORIES = [
  "Программирование",
  "Веб-разработка",
  "Мобильная разработка",
  "Аналитика данных",
  "Искусственный интеллект",
  "Языки",
  "Дизайн",
  "Маркетинг",
  "Менеджмент",
  "Математика",
];

export function normalizeCategory(value) {
  return (value || "").trim();
}
