import { useState, useMemo, useCallback, useEffect } from "react";
import AuthPage from "./components/AuthPage";
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
import { runCode, submitCode, traceCode } from "./api";

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
  // ─── Auth state ───
  const [user, setUser] = useState(() => {
    try {
      const stored = localStorage.getItem("cc_user");
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  });
  const [token, setToken] = useState(() => localStorage.getItem("cc_token"));

  const isAuthenticated = !!(user && token);

  const handleAuth = useCallback((userData, accessToken) => {
    setUser(userData);
    setToken(accessToken);
  }, []);

  const handleLogout = useCallback(() => {
    localStorage.removeItem("cc_token");
    localStorage.removeItem("cc_user");
    setUser(null);
    setToken(null);
  }, []);

  // ─── App state ───
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

  const handleRun = useCallback(async () => {
    setLoading("run");
    setError("");
    try {
      const result = await runCode(code);
      setRunOutput(result);
    } catch (err) {
      if (err.response?.status === 401) {
        handleLogout();
        return;
      }
      setRunOutput({
        stdout: "",
        stderr: err.response?.data?.detail || "Run failed. Is the backend running?",
        exit_code: -1,
      });
    } finally {
      setLoading("");
    }
  }, [code, handleLogout]);

  const handleAnalyze = useCallback(async () => {
    setLoading("analyze");
    setError("");
    try {
      const [result, traceResult] = await Promise.all([
        submitCode(Number(user.id), code),
        traceCode(code),
      ]);
      setFeedback(result);
      setExecutionTrace(traceResult.trace);
    } catch (err) {
      if (err.response?.status === 401) {
        handleLogout();
        return;
      }
      setError(err.response?.data?.detail || "Analysis failed. Is the backend running?");
    } finally {
      setLoading("");
    }
  }, [user, code, handleLogout]);

  // ─── Gate: show Auth page if not logged in ───
  if (!isAuthenticated) {
    return <AuthPage onAuth={handleAuth} />;
  }

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
        {/* User bar */}
        <div className="user-bar">
          <span className="user-greeting">
            👋 {user.name}
          </span>
          <button className="btn btn-logout" onClick={handleLogout}>
            Sign Out
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
