import { useState, useMemo, useCallback } from "react";
import CodeEditor from "./components/CodeEditor";
import OutputPanel from "./components/OutputPanel";
import FeedbackPanel from "./components/FeedbackPanel";
import HintsPanel from "./components/HintsPanel";
import LearningProgress from "./components/LearningProgress";
import { runCode, submitCode, createUser } from "./api";

const STARTER_CODE = `# Try submitting code with a conceptual mistake!
# Examples to try:
#   - A while True loop with no break
#   - A recursive function with no base case
#   - Using == instead of = for assignment

def count_down(n):
    while n > 0:
        print(n)
        n -= 1

count_down(5)`;

function App() {
  const [userId, setUserId] = useState(1);
  const [userCreated, setUserCreated] = useState(false);
  const [code, setCode] = useState(STARTER_CODE);
  const [runOutput, setRunOutput] = useState({
    stdout: "",
    stderr: "",
    exit_code: null,
  });
  const [feedback, setFeedback] = useState(null);
  const [loading, setLoading] = useState("");
  const [error, setError] = useState("");

  const profiles = useMemo(() => {
    if (!feedback?.profile) return [];
    return feedback.profile;
  }, [feedback]);

  const handleCreateUser = useCallback(async () => {
    setLoading("create");
    setError("");
    try {
      const user = await createUser(
        `Student ${Date.now()}`,
        `student${Date.now()}@codeconcept.dev`,
        "beginner"
      );
      setUserId(user.id);
      setUserCreated(true);
    } catch (err) {
      // If user already exists, just mark as created
      if (err.response?.status === 400 || err.response?.status === 409) {
        setUserCreated(true);
      } else {
        setError("Could not create user. Is the backend running on port 8000?");
      }
    } finally {
      setLoading("");
    }
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
        stderr:
          err.response?.data?.detail ||
          "Run failed. Is the backend running?",
        exit_code: -1,
      });
    } finally {
      setLoading("");
    }
  }, [code]);

  const handleAnalyze = useCallback(async () => {
    setLoading("analyze");
    setError("");
    try {
      const result = await submitCode(Number(userId), code);
      setFeedback(result);
    } catch (err) {
      if (err.response?.status === 404) {
        setError(
          "User not found. Click 'Create Learner' to set up a profile first."
        );
        setUserCreated(false);
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

  return (
    <div className="app-shell">
      {/* ===== Hero Header ===== */}
      <header className="hero">
        <div className="hero-badge">AI-Powered Learning Engine</div>
        <h1>CodeConcept</h1>
        <p>
          Detects conceptual mistakes in your code, explains the
          misunderstanding, and guides you with progressive hints — not just
          answers.
        </p>
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

          {/* Action Bar */}
          <div className="actions">
            <label>
              User ID
              <input
                type="number"
                min="1"
                value={userId}
                onChange={(e) => setUserId(e.target.value)}
              />
            </label>

            {!userCreated && (
              <button
                className="btn btn-create-user"
                onClick={handleCreateUser}
                disabled={!!loading}
              >
                {loading === "create" ? (
                  <>
                    <span className="spinner" /> Creating…
                  </>
                ) : (
                  "✦ Create Learner"
                )}
              </button>
            )}

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

        {/* ---- Right Column ---- */}
        <aside className="right-column">
          <FeedbackPanel feedback={feedback} />
          <HintsPanel feedback={feedback} />
          <LearningProgress profiles={profiles} />
        </aside>
      </main>
    </div>
  );
}

export default App;
