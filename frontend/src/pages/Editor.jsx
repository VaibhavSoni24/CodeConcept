import React, { useState, useMemo, useCallback, useEffect, useRef } from "react";
import CodeEditor from "../components/CodeEditor";
import OutputPanel from "../components/OutputPanel";
import FeedbackPanel from "../components/FeedbackPanel";
import HintsPanel from "../components/HintsPanel";
import LearningProgress from "../components/LearningProgress";
import TabBar from "../components/TabBar";
import CodeSmellsPanel from "../components/CodeSmellsPanel";
import ComplexityPanel from "../components/ComplexityPanel";
import ConceptsDetectedPanel from "../components/ConceptsDetectedPanel";
import ExecutionTracePanel from "../components/ExecutionTracePanel";
import FlowGraphPanel from "../components/FlowGraphPanel";
import ASTGraph from "../components/ASTGraph";
import SkillRadarChart from "../components/SkillRadarChart";
import RefactoringPanel from "../components/RefactoringPanel";
import { runCode, submitCode, traceCode, getProfile, formatCode } from "../api";
import { Upload, FileCode } from "lucide-react";

const SUPPORTED_LANGUAGES = [
  { id: "python", label: "Python", ext: ".py" },
  { id: "javascript", label: "JavaScript", ext: ".js" },
  { id: "cpp", label: "C++", ext: ".cpp" },
  { id: "java", label: "Java", ext: ".java" },
  { id: "go", label: "Go", ext: ".go" },
  { id: "rust", label: "Rust", ext: ".rs" },
];

const STARTER_CODE = {
  python: `# Try submitting code with a conceptual mistake!\ndef count_down(n):\n    while n > 0:\n        print(n)\n        n -= 1\ncount_down(5)`,
  javascript: `function countDown(n) {\n  while(n > 0) {\n    console.log(n);\n    n--;\n  }\n}\ncountDown(5);`,
  cpp: `#include <iostream>\nusing namespace std;\n\nint main() {\n  for(int i=5; i>0; i--) {\n    cout << i << endl;\n  }\n  return 0;\n}`,
  java: `public class Main {\n  public static void main(String[] args) {\n    for(int i=5; i>0; i--) {\n      System.out.println(i);\n    }\n  }\n}`,
  go: `package main\nimport "fmt"\n\nfunc main() {\n  for i := 5; i > 0; i-- {\n    fmt.Println(i)\n  }\n}`,
  rust: `fn main() {\n  let mut n = 5;\n  while n > 0 {\n    println!("{}", n);\n    n -= 1;\n  }\n}`,
};

const TABS = [
  { id: "diagnosis", label: "Diagnosis", icon: "⚡" },
  { id: "quality", label: "Code Quality", icon: "🔥" },
  { id: "ast", label: "AST", icon: "🌳" },
  { id: "trace", label: "Trace & Flow", icon: "🔍" },
  { id: "progress", label: "Progress", icon: "📊" },
];

function EditorPage({ user, token, handleLogout }) {
  const [language, setLanguage] = useState("python");
  const [code, setCode] = useState(STARTER_CODE["python"]);
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
  const [loadedProfile, setLoadedProfile] = useState({ profiles: [], skillScores: [] });
  const fileInputRef = useRef(null);

  useEffect(() => {
    if (user?.id) {
      getProfile(user.id).then((data) => {
        setLoadedProfile({
          profiles: data.profiles || [],
          skillScores: data.skill_scores || [],
        });
      }).catch(console.error);
    }
  }, [user?.id]);

  const profiles = useMemo(() => feedback?.profile || loadedProfile.profiles, [feedback, loadedProfile.profiles]);
  const skillScores = useMemo(() => feedback?.skill_scores || loadedProfile.skillScores, [feedback, loadedProfile.skillScores]);

  const handleLanguageChange = (e) => {
    const newLang = e.target.value;
    setLanguage(newLang);
    setCode(STARTER_CODE[newLang]);
    setFeedback(null);
    setRunOutput({ stdout: "", stderr: "", exit_code: null });
  };

  const handleFileUpload = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const fileName = file.name;
    const matchedLang = SUPPORTED_LANGUAGES.find(l => fileName.endsWith(l.ext));
    
    const reader = new FileReader();
    reader.onload = (event) => {
      setCode(event.target.result);
      if (matchedLang) setLanguage(matchedLang.id);
    };
    reader.readAsText(file);
    e.target.value = null; // reset input
  };

  const handleFormat = async () => {
    setLoading("format");
    setError("");
    try {
      const result = await formatCode(language, code);
      if (result && result.code) {
        setCode(result.code);
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Formatting failed. Required tools may not be installed.");
    } finally {
      setLoading("");
    }
  };

  const handleRun = useCallback(async () => {
    setLoading("run");
    setError("");
    try {
      const result = await runCode(language, code);
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
  }, [language, code, handleLogout]);

  const handleAnalyze = useCallback(async () => {
    setLoading("analyze");
    setError("");
    try {
      if (language === "python") {
        const [result, traceResult] = await Promise.all([
          submitCode(Number(user.id), language, code),
          traceCode(code),
        ]);
        setFeedback(result);
        setExecutionTrace(traceResult.trace);
      } else {
        const result = await submitCode(Number(user.id), language, code);
        setFeedback(result);
        setExecutionTrace(null);
      }
    } catch (err) {
      if (err.response?.status === 401) {
        handleLogout();
        return;
      }
      setError(err.response?.data?.detail || "Analysis failed. Is the backend running?");
    } finally {
      setLoading("");
    }
  }, [user, language, code, handleLogout]);

  return (
    <div className="flex flex-col h-full overflow-hidden max-h-screen">
      <header className="px-6 py-3 border-b border-[#333] flex items-center justify-between bg-[#1e1e2d]">
        <div className="flex items-center gap-4">
          <h1 className="text-lg font-bold">Workspace</h1>
          <select 
            value={language}
            onChange={handleLanguageChange}
            className="bg-[#2a2a3c] border border-[#444] text-sm text-gray-200 rounded px-2 py-1 outline-none"
          >
            {SUPPORTED_LANGUAGES.map(l => (
              <option key={l.id} value={l.id}>{l.label}</option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-3">
          <input 
            type="file" 
            ref={fileInputRef} 
            onChange={handleFileUpload} 
            className="hidden" 
            accept=".py,.js,.cpp,.cc,.java,.go,.rs"
          />
          <button 
            className="flex items-center gap-2 text-sm text-gray-300 hover:text-white transition-colors"
            onClick={() => fileInputRef.current?.click()}
          >
            <Upload size={16} /> Upload
          </button>
          
          <button 
            className="flex items-center gap-2 text-sm text-gray-300 hover:text-white transition-colors ml-2"
            onClick={handleFormat}
            disabled={!!loading}
          >
            <FileCode size={16} /> Format Code
          </button>
        </div>
      </header>

      {error && (
        <div
          className="card slide-down m-4"
          style={{
            background: "rgba(239, 68, 68, 0.1)",
            borderColor: "rgba(239, 68, 68, 0.3)",
            padding: "12px 16px",
            color: "#f87171",
            fontSize: "0.88rem",
          }}
        >
          ⚠ {error}
        </div>
      )}

      <main className="grid-layout flex-1 p-4 gap-6 min-h-[calc(100vh-4rem)]">
        {/* ---- Left Column ---- */}
        <section className="flex flex-col gap-4">
          <div className="flex-1 rounded-xl overflow-hidden border border-[#333]">
            <CodeEditor code={code} onChange={setCode} language={language === "python" ? "python" : language} />
          </div>

          <div className="actions flex gap-4">
            <button className="btn btn-run flex-1 py-3" onClick={handleRun} disabled={!!loading}>
              {loading === "run" ? (
                <><span className="spinner" /> Running…</>
              ) : (
                "▶ Run"
              )}
            </button>

            <button className="btn btn-analyze flex-1 py-3" onClick={handleAnalyze} disabled={!!loading}>
              {loading === "analyze" ? (
                <><span className="spinner" /> Analyzing…</>
              ) : (
                "🔍 Analyze"
              )}
            </button>
          </div>

          <div className="h-64">
            <OutputPanel output={runOutput} />
          </div>
        </section>

        {/* ---- Right Column with Tabs ---- */}
        <aside className="right-column flex flex-col h-full overflow-y-auto">
          <TabBar tabs={TABS} activeTab={activeTab} onChange={setActiveTab} />

          {/* Tab: Diagnosis */}
          {activeTab === "diagnosis" && (
            <div className="tab-content slide-down space-y-4">
              <FeedbackPanel feedback={feedback} />
              <HintsPanel feedback={feedback} />
              <RefactoringPanel suggestions={feedback?.refactoring_suggestions} />
            </div>
          )}

          {/* Tab: Code Quality */}
          {activeTab === "quality" && (
            <div className="tab-content slide-down space-y-4">
              <CodeSmellsPanel smells={feedback?.code_smells} />
              <ComplexityPanel complexity={feedback?.complexity} />
              <ConceptsDetectedPanel concepts={feedback?.concepts_detected} />
            </div>
          )}

          {/* Tab: AST */}
          {activeTab === "ast" && (
            <div className="tab-content slide-down space-y-4">
              <ASTGraph code={code} language={language} />
            </div>
          )}

          {/* Tab: Trace & Flow */}
          {activeTab === "trace" && (
            <div className="tab-content slide-down space-y-4">
              <ExecutionTracePanel trace={executionTrace} />
              <FlowGraphPanel flowGraph={feedback?.flow_graph} />
            </div>
          )}

          {/* Tab: Progress */}
          {activeTab === "progress" && (
            <div className="tab-content slide-down space-y-4">
              <SkillRadarChart skillScores={skillScores} />
              <LearningProgress profiles={profiles} />
            </div>
          )}
        </aside>
      </main>
    </div>
  );
}

export default EditorPage;
