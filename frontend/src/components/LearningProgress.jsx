function LearningProgress({ profiles }) {
  if (!profiles || profiles.length === 0) {
    return (
      <div className="card card-glow">
        <div className="card-header">
          <h2>
            <span className="card-icon cyan">📊</span>
            Learning Progress
          </h2>
        </div>
        <p className="progress-empty">
          No tracked concepts yet. Submit code to start tracking your progress.
        </p>
      </div>
    );
  }

  const getStatusClass = (level) => {
    switch (level) {
      case "strong":
        return "status-improving"; // reuse green-ish style
      case "improving":
        return "status-improving";
      case "beginner":
        return "status-beginner";
      default:
        return "status-beginner";
    }
  };

  const getFillClass = (level) => {
    switch (level) {
      case "strong":
        return "fill-improving"; // green
      case "improving":
        return "fill-beginner"; // amber
      case "beginner":
        return "fill-struggling"; // red/dim
      default:
        return "fill-beginner";
    }
  };

  // Use the real score (0-100) as the bar width percentage.
  // Falls back to a mastery-based estimate for legacy data without a score field.
  const getBarWidth = (item) => {
    if (typeof item.score === "number") {
      return Math.max(4, item.score); // at least 4% so bar is always visible
    }
    // Legacy fallback
    switch (item.mastery_level) {
      case "strong":
        return 90;
      case "improving":
        return 60;
      case "beginner":
        return 25;
      default:
        return 25;
    }
  };

  return (
    <div className="card card-glow fade-in">
      <div className="card-header">
        <h2>
          <span className="card-icon cyan">📊</span>
          Learning Progress
        </h2>
        <span className="chip chip-exit">
          {profiles.length} concepts
        </span>
      </div>

      <div className="progress-list">
        {profiles.map((item) => (
          <div key={item.concept} className="progress-item">
            <div className="progress-meta">
              <span className="progress-concept">{item.concept}</span>
              <span
                className={`progress-status ${getStatusClass(item.mastery_level)}`}
              >
                {item.mastery_level}
              </span>
            </div>
            <div className="progress-bar-track">
              <div
                className={`progress-bar-fill ${getFillClass(item.mastery_level)}`}
                style={{
                  width: `${getBarWidth(item)}%`,
                  transition: "width 0.5s ease",
                }}
              />
            </div>
            <span className="progress-detail">
              {typeof item.score === "number"
                ? `${item.score}% mastery · `
                : ""}
              {item.mistake_count} mistake{item.mistake_count !== 1 ? "s" : ""} recorded
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default LearningProgress;
