import { api } from "./client";

export async function registerUser(payload) {
  const { data } = await api.post("/auth/register", payload);
  return data;
}

export async function loginUser(payload) {
  const { data } = await api.post("/auth/login", payload);
  return data;
}

export async function getCurrentUser() {
  const { data } = await api.get("/auth/me");
  return data;
}

export async function updateProfile(payload) {
  const { data } = await api.patch("/users/me", payload);
  return data;
}

export async function uploadProfilePhoto(file) {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await api.post("/users/me/photo", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  return data;
}

export async function getMyCourses() {
  const { data } = await api.get("/users/me/courses");
  return data;
}
