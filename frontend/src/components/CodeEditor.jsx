import Editor from "@monaco-editor/react";

function CodeEditor({ code, onChange }) {
  return (
    <div className="card card-glow">
      <div className="card-header">
        <h2>
          <span className="card-icon purple">⌨</span>
          Code Editor
        </h2>
        <span className="chip chip-python">● Python</span>
      </div>
      <div className="editor-wrapper">
        <Editor
          height="400px"
          language="python"
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
