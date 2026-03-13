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
import { runCode, submitCode, traceCode, registerUser, loginUser } from "./api";

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
  const [authMode, setAuthMode] = useState("login"); // "login" | "register"
  const [authEmail, setAuthEmail] = useState("");
  const [authPassword, setAuthPassword] = useState("");
  const [authName, setAuthName] = useState("");
  const [user, setUser] = useState(null); // { id, name, token }

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

  const profiles = useMemo(() => feedback?.profile || [], [feedback]);
  const skillScores = useMemo(() => feedback?.skill_scores || [], [feedback]);

  // Restore session from localStorage on mount
  useEffect(() => {
    const token = localStorage.getItem("cc_token");
    const savedUser = localStorage.getItem("cc_user");
    if (token && savedUser) {
      try {
        setUser(JSON.parse(savedUser));
      } catch {
        localStorage.removeItem("cc_token");
        localStorage.removeItem("cc_user");
      }
    }
  }, []);

  const handleAuth = useCallback(async () => {
    setLoading("auth");
    setError("");
    try {
      let result;
      if (authMode === "register") {
        result = await registerUser(authName, authEmail, authPassword);
      } else {
        result = await loginUser(authEmail, authPassword);
      }
      const userData = { id: result.user_id, name: result.name, token: result.access_token };
      localStorage.setItem("cc_token", result.access_token);
      localStorage.setItem("cc_user", JSON.stringify(userData));
      setUser(userData);
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (typeof detail === "string") {
        setError(detail);
      } else {
        setError(authMode === "register" ? "Registration failed. Is the backend running?" : "Login failed. Check your credentials.");
      }
    } finally {
      setLoading("");
    }
  }, [authMode, authEmail, authPassword, authName]);

  const handleLogout = useCallback(() => {
    localStorage.removeItem("cc_token");
    localStorage.removeItem("cc_user");
    setUser(null);
    setFeedback(null);
    setExecutionTrace(null);
    setError("");
  }, []);

  const handleRun = useCallback(async () => {
    setLoading("run");
    setError("");
    try {
      const result = await runCode(code);
      setRunOutput(result);
    } catch (err) {
      setRunOutput({
        stdout: "",
        stderr: err.response?.data?.detail || "Run failed. Is the backend running?",
        exit_code: -1,
      });
    } finally {
      setLoading("");
    }
  }, [code]);

  const handleAnalyze = useCallback(async () => {
    if (!user) {
      setError("Please log in first.");
      return;
    }
    setLoading("analyze");
    setError("");
    try {
      // Run analysis + trace in parallel
      const [result, traceResult] = await Promise.all([
        submitCode(user.id, code),
        traceCode(code),
      ]);
      setFeedback(result);
      setExecutionTrace(traceResult.trace);
    } catch (err) {
      if (err.response?.status === 404) {
        setError("User not found. Please log in again.");
        handleLogout();
      } else {
        setError(err.response?.data?.detail || "Analysis failed. Is the backend running?");
      }
    } finally {
      setLoading("");
    }
  }, [user, code, handleLogout]);

  // =================== AUTH SCREEN ===================
  if (!user) {
    return (
      <div className="app-shell">
        <header className="hero">
          <div className="hero-badge">AI-Powered Learning Engine</div>
          <h1>CodeConcept</h1>
          <p>Deep code reasoning, behavioral analysis, and learning analytics — not just debugging.</p>
        </header>

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

        <div className="card card-glow" style={{ maxWidth: 420, margin: "0 auto" }}>
          <div className="card-header">
            <h2>
              <span className="card-icon amber">🔐</span>
              {authMode === "login" ? "Login" : "Register"}
            </h2>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "12px", padding: "4px 0" }}>
            {authMode === "register" && (
              <input
                type="text"
                placeholder="Full Name"
                value={authName}
                onChange={(e) => setAuthName(e.target.value)}
                className="auth-input"
              />
            )}
            <input
              type="email"
              placeholder="Email"
              value={authEmail}
              onChange={(e) => setAuthEmail(e.target.value)}
              className="auth-input"
            />
            <input
              type="password"
              placeholder="Password"
              value={authPassword}
              onChange={(e) => setAuthPassword(e.target.value)}
              className="auth-input"
              onKeyDown={(e) => e.key === "Enter" && handleAuth()}
            />

            <button
              className="btn btn-analyze"
              onClick={handleAuth}
              disabled={!!loading}
              style={{ width: "100%", marginTop: 4 }}
            >
              {loading === "auth" ? (
                <><span className="spinner" /> {authMode === "login" ? "Logging in…" : "Registering…"}</>
              ) : (
                authMode === "login" ? "🔓 Login" : "✦ Register"
              )}
            </button>

            <p style={{ textAlign: "center", fontSize: "0.85rem", color: "#94a3b8", margin: 0 }}>
              {authMode === "login" ? (
                <>Don't have an account?{" "}
                  <button
                    className="link-btn"
                    onClick={() => { setAuthMode("register"); setError(""); }}
                  >
                    Register
                  </button>
                </>
              ) : (
                <>Already have an account?{" "}
                  <button
                    className="link-btn"
                    onClick={() => { setAuthMode("login"); setError(""); }}
                  >
                    Login
                  </button>
                </>
              )}
            </p>
          </div>
        </div>
      </div>
    );
  }

  // =================== MAIN APP ===================
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
        <div className="user-bar">
          <span className="user-greeting">👋 {user.name}</span>
          <button className="btn btn-logout" onClick={handleLogout}>Logout</button>
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
            <button className="btn btn-run" onClick={handleRun} disabled={!!loading}>
              {loading === "run" ? (
                <><span className="spinner" /> Running…</>
              ) : (
                "▶ Run"
              )}
            </button>

            <button className="btn btn-analyze" onClick={handleAnalyze} disabled={!!loading}>
              {loading === "analyze" ? (
                <><span className="spinner" /> Analyzing…</>
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
              <RefactoringPanel suggestions={feedback?.refactoring_suggestions} />
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
