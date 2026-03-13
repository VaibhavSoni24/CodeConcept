import axios from "axios";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
  timeout: 15000,
});

// Attach JWT token to every request if available
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("cc_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// On 401, clear stored auth so UI falls back to login
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("cc_token");
      localStorage.removeItem("cc_user");
    }
    return Promise.reject(err);
  }
);

// ---------- Auth ----------
export async function registerUser(name, email, password, level = "beginner") {
  const res = await api.post("/auth/register", { name, email, password, level });
  return res.data;
}

export async function loginUser(email, password) {
  const res = await api.post("/auth/login", { email, password });
  return res.data;
}

export async function getMe() {
  const res = await api.get("/auth/me");
  return res.data;
}

// ---------- Existing ----------
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
