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
export async function runCode(language, code) {
  const res = await api.post("/run-code", { language, code });
  return res.data;
}

export async function submitCode(userId, language, code, options = {}) {
  const { fileName = null, editCount = 0 } = options;
  const res = await api.post("/submit-code", {
    user_id: userId,
    language,
    code,
    file_name: fileName,
    edit_count: editCount,
  });
  return res.data;
}

export async function formatCode(language, code) {
  const res = await api.post("/format-code", { language, code });
  return res.data;
}

export async function getASTGraph(language, code) {
  const res = await api.post("/ast-graph", { language, code });
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

export async function getUserSubmissions(userId) {
  const res = await api.get(`/users/${userId}/submissions`);
  return res.data;
}

export async function getNotes(userId) {
  const res = await api.get(`/users/${userId}/notes`);
  return res.data;
}

export async function createNote(submissionId, content) {
  const res = await api.post("/notes", { submission_id: submissionId, content });
  return res.data;
}

export async function traceCode(language, code) {
  const res = await api.post("/trace", { language, code });
  return res.data;
}

export async function getKnowledgeRecommendations(userId) {
  const res = await api.get(`/users/${userId}/knowledge-recommendations`);
  return res.data;
}

export async function getGlobalKnowledgeSummary() {
  const res = await api.get(`/knowledge/global-summary`);
  return res.data;
}

export async function getUserCredits(userId) {
  const res = await api.get(`/users/${userId}/credits`);
  return res.data;
}

// ---------- Billing (dummy payment mode) ----------
export async function getBillingPlans() {
  const res = await api.get(`/billing/plans`);
  return res.data;
}

export async function getUserSubscription(userId) {
  const res = await api.get(`/billing/users/${userId}/subscription`);
  return res.data;
}

export async function subscribePlan(userId, planKey) {
  const res = await api.post(`/billing/users/${userId}/subscribe/${planKey}`);
  return res.data;
}

export async function topupCredits(userId, packKey) {
  const res = await api.post(`/billing/users/${userId}/topup/${packKey}`);
  return res.data;
}

export async function getBillingMetrics() {
  const res = await api.get(`/billing/metrics`);
  return res.data;
}

export default api;
