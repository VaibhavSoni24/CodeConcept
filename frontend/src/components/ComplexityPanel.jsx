function ComplexityPanel({ complexity }) {
  if (!complexity) {
    return (
      <div className="card card-glow">
        <div className="card-header">
          <h2>
            <span className="card-icon cyan">📐</span>
            Code Complexity
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

  const getTimeColor = (val) => {
    if (!val) return "var(--green)";
    if (val.includes("n²") || val.includes("n^2")) return "var(--amber)";
    if (val.includes("n³") || val.includes("n^3") || val.includes("2^n")) return "var(--red)";
    if (val === "O(1)" || val.includes("log")) return "var(--green)";
    return "var(--green)";
  };

  const metrics = [
    {
      label: "Time Complexity",
      value: complexity.time_complexity || "O(1)",
      icon: "⏱️",
      color: getTimeColor(complexity.time_complexity),
    },
    {
      label: "Space Complexity",
      value: complexity.space_complexity || "O(1)",
      icon: "💾",
      color: getTimeColor(complexity.space_complexity),
    },
    {
      label: "Cyclomatic Complexity",
      value: complexity.cyclomatic_complexity ?? "—",
      icon: "🔄",
      color: getColor(complexity.cyclomatic_complexity ?? 0, [5, 10]),
    },
    {
      label: "Loop Depth",
      value: complexity.loop_depth ?? "—",
      icon: "🔁",
      color: getColor(complexity.loop_depth ?? 0, [2, 4]),
    },
    {
      label: "LOC",
      value: complexity.loc ?? "—",
      icon: "📝",
      color: getColor(complexity.loc ?? 0, [100, 300]),
    },
    {
      label: "Functions",
      value: complexity.function_count ?? "—",
      icon: "🔧",
      color: "var(--cyan)",
    },
    {
      label: "Branch Count",
      value: complexity.branch_count ?? "—",
      icon: "🌿",
      color: getColor(complexity.branch_count ?? 0, [4, 8]),
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
          Code Complexity
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
