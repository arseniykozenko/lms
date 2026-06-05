export function isTeacherRole(role) {
  return role === "teacher" || role === "admin";
}

export function roleLabel(role) {
  if (role === "admin") return "Администратор";
  if (role === "teacher") return "Преподаватель";
  return "Студент";
}

export function profileRoleLabel(role) {
  if (role === "admin") return "Профиль администратора";
  if (role === "teacher") return "Профиль преподавателя";
  return "Профиль студента";
}
