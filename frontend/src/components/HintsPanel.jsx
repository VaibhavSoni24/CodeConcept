import { useState, useEffect } from "react";

function HintsPanel({ feedback }) {
  const [revealedCount, setRevealedCount] = useState(0);

  // Reset hints when feedback changes
  useEffect(() => {
    setRevealedCount(0);
  }, [feedback]);

  if (!feedback) {
    return (
      <div className="card card-glow">
        <div className="card-header">
          <h2>
            <span className="card-icon purple">🔮</span>
            Progressive Hints
          </h2>
        </div>
        <p className="hint-empty">Hints will appear after analysis.</p>
      </div>
    );
  }

  const hints = [
    feedback.hint_level_1,
    feedback.hint_level_2,
    feedback.hint_level_3,
  ].filter(Boolean);

  const revealNext = () => {
    if (revealedCount < hints.length) {
      setRevealedCount((prev) => prev + 1);
    }
  };

  return (
    <div className="card card-glow fade-in">
      <div className="card-header">
        <h2>
          <span className="card-icon purple">🔮</span>
          Progressive Hints
        </h2>
        <span className="chip chip-exit">
          {revealedCount}/{hints.length}
        </span>
      </div>

      <ul className="hints-list">
        {hints.map((hint, i) => {
          const isRevealed = i < revealedCount;
          const isNext = i === revealedCount;

          return (
            <li
              key={i}
              className={`hint-item ${isRevealed ? "revealed slide-down" : "locked"}`}
              onClick={isNext ? revealNext : undefined}
              title={isNext ? "Click to reveal this hint" : ""}
            >
              <span
                className={`hint-level ${isRevealed ? "active" : "locked"}`}
              >
                {i + 1}
              </span>
              {isRevealed ? (
                <span className="hint-text">{hint}</span>
              ) : (
                <span className="hint-locked-text">
                  {isNext
                    ? "🔒 Click to reveal hint…"
                    : "🔒 Reveal previous hints first"}
                </span>
              )}
            </li>
          );
        })}
      </ul>

      {revealedCount < hints.length && (
        <button
          className="btn btn-analyze"
          onClick={revealNext}
          style={{ marginTop: "10px", width: "100%" }}
        >
          Reveal Hint {revealedCount + 1}
        </button>
      )}
    </div>
  );
}

export default HintsPanel;
