import { useState, useMemo, useCallback, useEffect } from "react";
import CodeEditor from "./components/CodeEditor";
import OutputPanel from "./components/OutputPanel";
import FeedbackPanel from "./components/FeedbackPanel";
import HintsPanel from "./components/HintsPanel";
import LearningProgress from "./components/LearningProgress";
import TabBar from "./components/TabBar";
import CodeSmellsPanel from "./components/CodeSmellsPanel";
import ComplexityPanel from "./components/ComplexityPanel";
import ConceptsDetectedPanel from "./components/ConceptsDetectedPanel";
import ExecutionTracePanel from "./components/ExecutionTracePanel";
import FlowGraphPanel from "./components/FlowGraphPanel";
import SkillRadarChart from "./components/SkillRadarChart";
import RefactoringPanel from "./components/RefactoringPanel";
import {
  runCode,
  submitCode,
  traceCode,
  loginUser,
  registerUser,
  logoutUser,
  getStoredAuth,
} from "./api";

const STARTER_CODE = `# Try submitting code with a conceptual mistake!
# Examples:
#   - while True without break
#   - def f(x=[]): mutable default
#   - range(len(arr)+1): off-by-one

def count_down(n):
    while n > 0:
        print(n)
        n -= 1

count_down(5)`;

const TABS = [
  { id: "diagnosis", label: "Diagnosis", icon: "⚡" },
  { id: "quality", label: "Code Quality", icon: "🔥" },
  { id: "trace", label: "Trace & Flow", icon: "🔍" },
  { id: "progress", label: "Progress", icon: "📊" },
];

function App() {
  // Auth state
  const [authUser, setAuthUser] = useState(() => getStoredAuth());
  const [authMode, setAuthMode] = useState("login"); // "login" | "register"
  const [authForm, setAuthForm] = useState({
    name: "",
    email: "",
    password: "",
  });
  const [authLoading, setAuthLoading] = useState(false);
  const [authError, setAuthError] = useState("");

  // App state
  const [code, setCode] = useState(STARTER_CODE);
  const [runOutput, setRunOutput] = useState({
    stdout: "",
    stderr: "",
    exit_code: null,
  });
  const [feedback, setFeedback] = useState(null);
  const [executionTrace, setExecutionTrace] = useState(null);
  const [loading, setLoading] = useState("");
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState("diagnosis");

  const userId = authUser?.user_id;
  const profiles = useMemo(() => feedback?.profile || [], [feedback]);
  const skillScores = useMemo(() => feedback?.skill_scores || [], [feedback]);

  // --- Auth handlers ---
  const handleAuth = useCallback(
    async (e) => {
      e.preventDefault();
      setAuthLoading(true);
      setAuthError("");
      try {
        let data;
        if (authMode === "register") {
          data = await registerUser(
            authForm.name,
            authForm.email,
            authForm.password
          );
        } else {
          data = await loginUser(authForm.email, authForm.password);
        }
        setAuthUser({
          user_id: data.user_id,
          name: data.name,
          email: data.email,
        });
      } catch (err) {
        const msg =
          err.response?.data?.detail ||
          "Authentication failed. Is the backend running on port 8000?";
        setAuthError(msg);
      } finally {
        setAuthLoading(false);
      }
    },
    [authMode, authForm]
  );

  const handleLogout = useCallback(() => {
    logoutUser();
    setAuthUser(null);
    setFeedback(null);
    setExecutionTrace(null);
  }, []);

  // --- App handlers ---
  const handleRun = useCallback(async () => {
    setLoading("run");
    setError("");
    try {
      const result = await runCode(code);
      setRunOutput(result);
    } catch (err) {
      setRunOutput({
        stdout: "",
        stderr:
          err.response?.data?.detail || "Run failed. Is the backend running?",
        exit_code: -1,
      });
    } finally {
      setLoading("");
    }
  }, [code]);

  const handleAnalyze = useCallback(async () => {
    if (!userId) return;
    setLoading("analyze");
    setError("");
    try {
      const [result, traceResult] = await Promise.all([
        submitCode(Number(userId), code),
        traceCode(code),
      ]);
      setFeedback(result);
      setExecutionTrace(traceResult.trace);
    } catch (err) {
      if (err.response?.status === 404) {
        setError("User not found. Please log in again.");
      } else {
        setError(
          err.response?.data?.detail ||
            "Analysis failed. Is the backend running?"
        );
      }
    } finally {
      setLoading("");
    }
  }, [userId, code]);

  // --- Auth screen ---
  if (!authUser) {
    return (
      <div className="app-shell">
        <header className="hero">
          <div className="hero-badge">AI-Powered Learning Engine</div>
          <h1>CodeConcept</h1>
          <p>
            Deep code reasoning, behavioral analysis, and learning analytics —
            not just debugging.
          </p>
        </header>

        <div className="auth-container">
          <div className="card card-glow auth-card">
            <div className="auth-tabs">
              <button
                className={`auth-tab ${authMode === "login" ? "active" : ""}`}
                onClick={() => {
                  setAuthMode("login");
                  setAuthError("");
                }}
              >
                Login
              </button>
              <button
                className={`auth-tab ${authMode === "register" ? "active" : ""}`}
                onClick={() => {
                  setAuthMode("register");
                  setAuthError("");
                }}
              >
                Register
              </button>
            </div>

            {authError && <div className="auth-error">⚠ {authError}</div>}

            <form onSubmit={handleAuth} className="auth-form">
              {authMode === "register" && (
                <label className="auth-label">
                  Name
                  <input
                    type="text"
                    className="auth-input"
                    value={authForm.name}
                    onChange={(e) =>
                      setAuthForm({ ...authForm, name: e.target.value })
                    }
                    required
                    minLength={2}
                    placeholder="Your name"
                  />
                </label>
              )}
              <label className="auth-label">
                Email
                <input
                  type="email"
                  className="auth-input"
                  value={authForm.email}
                  onChange={(e) =>
                    setAuthForm({ ...authForm, email: e.target.value })
                  }
                  required
                  placeholder="you@example.com"
                />
              </label>
              <label className="auth-label">
                Password
                <input
                  type="password"
                  className="auth-input"
                  value={authForm.password}
                  onChange={(e) =>
                    setAuthForm({ ...authForm, password: e.target.value })
                  }
                  required
                  minLength={6}
                  placeholder="••••••••"
                />
              </label>
              <button
                type="submit"
                className="btn btn-analyze auth-submit"
                disabled={authLoading}
              >
                {authLoading ? (
                  <>
                    <span className="spinner" /> Please wait…
                  </>
                ) : authMode === "login" ? (
                  "🔑 Login"
                ) : (
                  "✦ Create Account"
                )}
              </button>
            </form>
          </div>
        </div>
      </div>
    );
  }

  // --- Main app (authenticated) ---
  return (
    <div className="app-shell">
      {/* ===== Hero Header ===== */}
      <header className="hero">
        <div className="hero-badge">AI-Powered Learning Engine</div>
        <h1>CodeConcept</h1>
        <p>
          Deep code reasoning, behavioral analysis, and learning analytics —
          not just debugging.
        </p>
        <div className="auth-bar">
          <span className="auth-user-info">
            👤 {authUser.name} ({authUser.email})
          </span>
          <button className="btn btn-logout" onClick={handleLogout}>
            Logout
          </button>
        </div>
      </header>

      {/* ===== Error Banner ===== */}
      {error && (
        <div
          className="card slide-down"
          style={{
            background: "rgba(239, 68, 68, 0.1)",
            borderColor: "rgba(239, 68, 68, 0.3)",
            padding: "12px 16px",
            marginBottom: "14px",
            color: "#f87171",
            fontSize: "0.88rem",
          }}
        >
          ⚠ {error}
        </div>
      )}

      {/* ===== Main Grid ===== */}
      <main className="grid-layout">
        {/* ---- Left Column ---- */}
        <section>
          <CodeEditor code={code} onChange={setCode} />

          <div className="actions">
            <button
              className="btn btn-run"
              onClick={handleRun}
              disabled={!!loading}
            >
              {loading === "run" ? (
                <>
                  <span className="spinner" /> Running…
                </>
              ) : (
                "▶ Run"
              )}
            </button>

            <button
              className="btn btn-analyze"
              onClick={handleAnalyze}
              disabled={!!loading}
            >
              {loading === "analyze" ? (
                <>
                  <span className="spinner" /> Analyzing…
                </>
              ) : (
                "🔍 Analyze"
              )}
            </button>
          </div>

          <OutputPanel output={runOutput} />
        </section>

        {/* ---- Right Column with Tabs ---- */}
        <aside className="right-column">
          <TabBar tabs={TABS} activeTab={activeTab} onChange={setActiveTab} />

          {/* Tab: Diagnosis */}
          {activeTab === "diagnosis" && (
            <div className="tab-content slide-down">
              <FeedbackPanel feedback={feedback} />
              <HintsPanel feedback={feedback} />
              <RefactoringPanel
                suggestions={feedback?.refactoring_suggestions}
              />
            </div>
          )}

          {/* Tab: Code Quality */}
          {activeTab === "quality" && (
            <div className="tab-content slide-down">
              <CodeSmellsPanel smells={feedback?.code_smells} />
              <ComplexityPanel complexity={feedback?.complexity} />
              <ConceptsDetectedPanel concepts={feedback?.concepts_detected} />
            </div>
          )}

          {/* Tab: Trace & Flow */}
          {activeTab === "trace" && (
            <div className="tab-content slide-down">
              <ExecutionTracePanel trace={executionTrace} />
              <FlowGraphPanel flowGraph={feedback?.flow_graph} />
            </div>
          )}

          {/* Tab: Progress */}
          {activeTab === "progress" && (
            <div className="tab-content slide-down">
              <SkillRadarChart skillScores={skillScores} />
              <LearningProgress profiles={profiles} />
            </div>
          )}
        </aside>
      </main>
    </div>
  );
}

export default App;
