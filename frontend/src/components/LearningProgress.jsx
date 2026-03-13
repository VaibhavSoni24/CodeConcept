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
      case "struggling":
        return "status-struggling";
      case "beginner":
        return "status-beginner";
      case "improving":
        return "status-improving";
      default:
        return "status-beginner";
    }
  };

  const getFillClass = (level) => {
    switch (level) {
      case "struggling":
        return "fill-struggling";
      case "beginner":
        return "fill-beginner";
      case "improving":
        return "fill-improving";
      default:
        return "fill-beginner";
    }
  };

  const getBarWidth = (level, count) => {
    switch (level) {
      case "struggling":
        return Math.min(30 + count * 5, 95);
      case "beginner":
        return Math.min(45 + count * 3, 80);
      case "improving":
        return Math.max(10, 30 - count * 3);
      default:
        return 50;
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
                  width: `${getBarWidth(item.mastery_level, item.mistake_count)}%`,
                }}
              />
            </div>
            <span className="progress-detail">
              {item.mistake_count} mistake{item.mistake_count !== 1 ? "s" : ""} recorded
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default LearningProgress;
