function LearningProgress({ skillScores }) {
  if (!skillScores || skillScores.length === 0) {
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

  const getStatusClass = (score) => {
    if (score >= 80) return "status-improving";
    if (score >= 40) return "status-beginner";
    return "status-struggling";
  };

  const getFillClass = (score) => {
    if (score >= 80) return "fill-improving";
    if (score >= 40) return "fill-beginner";
    return "fill-struggling";
  };

  const getMasteryLabel = (score) => {
    if (score >= 80) return "Mastering";
    if (score >= 40) return "Beginner";
    return "Struggling";
  };

  return (
    <div className="card card-glow fade-in">
      <div className="card-header">
        <h2>
          <span className="card-icon cyan">📊</span>
          Learning Progress
        </h2>
        <span className="chip chip-exit">
          {skillScores.length} concepts
        </span>
      </div>

      <div className="progress-list">
        {skillScores.map((item) => {
          const mistakes = item.total_usage - item.correct_usage;
          return (
            <div key={item.concept} className="progress-item">
              <div className="progress-meta">
                <span className="progress-concept">{item.concept.replace(/_/g, ' ')}</span>
                <span
                  className={`progress-status ${getStatusClass(item.score)}`}
                >
                  {getMasteryLabel(item.score)} ({item.score}%)
                </span>
              </div>
              <div className="progress-bar-track">
                <div
                  className={`progress-bar-fill ${getFillClass(item.score)}`}
                  style={{
                    width: `${Math.max(5, item.score)}%`,
                  }}
                />
              </div>
              <span className="progress-detail">
                {item.correct_usage} correct / {item.total_usage} uses ({mistakes} mistake{mistakes !== 1 ? "s" : ""})
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default LearningProgress;
