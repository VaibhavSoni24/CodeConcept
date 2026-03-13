function FeedbackPanel({ feedback }) {
  if (!feedback) {
    return (
      <div className="card card-glow">
        <div className="card-header">
          <h2>
            <span className="card-icon amber">⚡</span>
            Diagnosis
          </h2>
        </div>
        <p className="feedback-empty">
          Submit your code to receive an AI-powered concept diagnosis.
        </p>
      </div>
    );
  }

  return (
    <div className="card card-glow fade-in">
      <div className="card-header">
        <h2>
          <span className="card-icon amber">⚡</span>
          Diagnosis
        </h2>
      </div>

      <div className="feedback-section">
        <span className="feedback-label">Concept</span>
        <span className="concept-badge">{feedback.concept || "General"}</span>
      </div>

      <div className="feedback-divider" />

      <div className="feedback-section">
        <span className="feedback-label">Mistake Type</span>
        <span className="mistake-badge">
          {feedback.mistake_type || "Unknown"}
        </span>
      </div>

      <div className="feedback-divider" />

      <div className="feedback-section">
        <span className="feedback-label">Explanation</span>
        <p className="feedback-value">
          {feedback.explanation || "No explanation available."}
        </p>
      </div>

      {feedback.practice && (
        <div className="practice-box">
          <span className="feedback-label">💡 Practice Challenge</span>
          <p className="feedback-value">{feedback.practice}</p>
        </div>
      )}
    </div>
  );
}

export default FeedbackPanel;
