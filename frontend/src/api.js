import axios from "axios";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
  timeout: 15000,
});

export async function runCode(code) {
  const res = await api.post("/run-code", { code });
  return res.data;
}

export async function submitCode(userId, code) {
  const res = await api.post("/submit-code", {
    user_id: userId,
    language: "python",
    code,
  });
  return res.data;
}

export async function createUser(name, email, level) {
  const res = await api.post("/users", { name, email, level });
  return res.data;
}

export async function getProfile(userId) {
  const res = await api.get(`/profiles/${userId}`);
  return res.data;
}

export async function traceCode(code) {
  const res = await api.post("/trace", { code });
  return res.data;
}

export default api;
