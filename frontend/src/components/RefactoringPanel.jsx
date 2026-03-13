function RefactoringPanel({ suggestions }) {
  let validSuggestions = [];
  if (Array.isArray(suggestions)) {
    validSuggestions = suggestions;
  } else if (typeof suggestions === 'string') {
    validSuggestions = [suggestions];
  }

  if (validSuggestions.length === 0) {
    return null;
  }

  return (
    <div className="card card-glow fade-in">
      <div className="card-header">
        <h2>
          <span className="card-icon green">🔧</span>
          Refactoring Suggestions
        </h2>
      </div>
      <ol className="refactoring-list">
        {validSuggestions.map((suggestion, i) => (
          <li key={i} className="refactoring-item">
            {suggestion}
          </li>
        ))}
      </ol>
    </div>
  );
}

export default RefactoringPanel;
