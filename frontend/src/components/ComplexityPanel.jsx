function ComplexityPanel({ complexity }) {
  if (!complexity) {
    return (
      <div className="card card-glow">
        <div className="card-header">
          <h2>
            <span className="card-icon cyan">📐</span>
            Complexity
          </h2>
        </div>
        <p className="feedback-empty">Submit code to see complexity metrics.</p>
      </div>
    );
  }

  const getColor = (value, thresholds) => {
    if (value >= thresholds[1]) return "var(--red)";
    if (value >= thresholds[0]) return "var(--amber)";
    return "var(--green)";
  };

  const metrics = [
    {
      label: "Cyclomatic Complexity",
      value: complexity.cyclomatic_complexity,
      icon: "🔄",
      color: getColor(complexity.cyclomatic_complexity, [5, 10]),
    },
    {
      label: "Loop Depth",
      value: complexity.loop_depth,
      icon: "🔁",
      color: getColor(complexity.loop_depth, [2, 4]),
    },
    {
      label: "Branch Count",
      value: complexity.branch_count,
      icon: "🌿",
      color: getColor(complexity.branch_count, [4, 8]),
    },
    {
      label: "Recursion",
      value: complexity.has_recursion ? "Yes" : "No",
      icon: "♻️",
      color: complexity.has_recursion ? "var(--amber)" : "var(--green)",
    },
  ];

  return (
    <div className="card card-glow fade-in">
      <div className="card-header">
        <h2>
          <span className="card-icon cyan">📐</span>
          Complexity
        </h2>
      </div>
      <div className="metrics-grid">
        {metrics.map((m) => (
          <div key={m.label} className="metric-card">
            <span className="metric-icon">{m.icon}</span>
            <span className="metric-value" style={{ color: m.color }}>
              {m.value}
            </span>
            <span className="metric-label">{m.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default ComplexityPanel;
