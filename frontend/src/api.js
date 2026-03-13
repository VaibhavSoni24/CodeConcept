import axios from "axios";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
  timeout: 30000,
});

// --- Token helpers ---
function getToken() {
  return localStorage.getItem("cc_token");
}
export function setToken(token) {
  if (token) localStorage.setItem("cc_token", token);
  else localStorage.removeItem("cc_token");
}
export function getStoredAuth() {
  const token = getToken();
  const raw = localStorage.getItem("cc_user");
  if (!token || !raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}
export function setStoredAuth(data) {
  if (data) localStorage.setItem("cc_user", JSON.stringify(data));
  else localStorage.removeItem("cc_user");
}

// Attach JWT to every request automatically
api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// --- Auth API ---
export async function loginUser(email, password) {
  const res = await api.post("/auth/login", { email, password });
  setToken(res.data.access_token);
  setStoredAuth({ user_id: res.data.user_id, name: res.data.name, email: res.data.email });
  return res.data;
}

export async function registerUser(name, email, password, level = "beginner") {
  const res = await api.post("/auth/register", { name, email, password, level });
  setToken(res.data.access_token);
  setStoredAuth({ user_id: res.data.user_id, name: res.data.name, email: res.data.email });
  return res.data;
}

export function logoutUser() {
  setToken(null);
  setStoredAuth(null);
}

// --- Existing APIs ---
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
