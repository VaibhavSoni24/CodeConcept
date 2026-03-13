function CodeSmellsPanel({ smells }) {
  if (!smells || smells.length === 0) {
    return (
      <div className="card card-glow">
        <div className="card-header">
          <h2>
            <span className="card-icon amber">🔥</span>
            Code Smells
          </h2>
        </div>
        <p className="feedback-empty">No code smells detected. Clean code!</p>
      </div>
    );
  }

  const getSeverityClass = (severity) => {
    switch (severity) {
      case "high":
        return "severity-high";
      case "medium":
        return "severity-medium";
      default:
        return "severity-low";
    }
  };

  return (
    <div className="card card-glow fade-in">
      <div className="card-header">
        <h2>
          <span className="card-icon amber">🔥</span>
          Code Smells
        </h2>
        <span className="chip chip-exit">{smells.length} found</span>
      </div>
      <div className="smell-list">
        {smells.map((smell, i) => (
          <div key={i} className="smell-item">
            <span className={`smell-severity ${getSeverityClass(smell.severity)}`}>
              {smell.severity}
            </span>
            <div className="smell-info">
              <span className="smell-type">{smell.type}</span>
              <span className="smell-message">{smell.message}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default CodeSmellsPanel;
