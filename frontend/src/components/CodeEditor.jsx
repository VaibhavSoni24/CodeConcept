import Editor from "@monaco-editor/react";

function CodeEditor({ code, onChange, language = "python" }) {
  const displayLang = language === "javascript" ? "JavaScript" : 
                      language === "cpp" ? "C++" : 
                      language.charAt(0).toUpperCase() + language.slice(1);

  return (
    <div className="card card-glow h-full flex flex-col">
      <div className="card-header shrink-0">
        <h2>
          <span className="card-icon purple">⌨</span>
          Code Editor
        </h2>
        <span className={`chip chip-${language}`}>● {displayLang}</span>
      </div>
      <div className="editor-wrapper flex-1 min-h-0">
        <Editor
          height="100%"
          language={language}
          theme="vs-dark"
          value={code}
          onChange={(value) => onChange(value || "")}
          options={{
            fontSize: 14,
            fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
            minimap: { enabled: false },
            smoothScrolling: true,
            scrollBeyondLastLine: false,
            padding: { top: 12, bottom: 12 },
            lineHeight: 22,
            renderLineHighlight: "gutter",
            bracketPairColorization: { enabled: true },
            automaticLayout: true,
          }}
        />
      </div>
    </div>
  );
}

export default CodeEditor;
