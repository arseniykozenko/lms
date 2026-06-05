export function getUserDisplayName(user) {
  if (!user) return "";
  const firstName = (user.first_name || "").trim();
  const secondName = (user.second_name || "").trim();
  const full = [firstName, secondName].filter(Boolean).join(" ").trim();
  const legacyFullName = (user.full_name || "").trim();
  return full || legacyFullName || user.email || "Пользователь";
}
