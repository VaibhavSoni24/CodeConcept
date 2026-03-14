function OutputPanel({ output }) {
  const hasOutput = output.stdout || output.stderr;
  const exitCode = output.exit_code;

  return (
    <div className="card card-glow h-full flex flex-col">
      <div className="card-header shrink-0">
        <h2>
          <span className="card-icon green">▶</span>
          Output
        </h2>
        {exitCode !== null && (
          <span className="chip chip-exit">
            exit: {exitCode}
          </span>
        )}
      </div>
      <div className="terminal flex-1 overflow-y-auto" style={{ maxHeight: "none" }}>
        {!hasOutput && exitCode === null ? (
          <span className="terminal-empty">
            Run your code to see output here…
          </span>
        ) : (
          <>
            {output.stdout && <span>{output.stdout}</span>}
            {output.stderr && (
              <span className="terminal-error">{output.stderr}</span>
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default OutputPanel;
