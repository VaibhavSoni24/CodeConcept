function ConceptsDetectedPanel({ concepts }) {
  if (!concepts || concepts.length === 0) {
    return null;
  }

  const iconMap = {
    loops: "🔁",
    conditionals: "🔀",
    recursion: "♻️",
    functions: "⚙️",
    classes: "🏗️",
    list_comprehensions: "📋",
    dict_comprehensions: "📖",
    set_comprehensions: "🔢",
    generators: "⚡",
    exception_handling: "🛡️",
    lambda_functions: "λ",
    decorators: "🎨",
    return_values: "↩️",
    imports: "📦",
    async: "⏳",
  };

  return (
    <div className="card card-glow fade-in">
      <div className="card-header">
        <h2>
          <span className="card-icon green">🧩</span>
          Concepts Detected
        </h2>
        <span className="chip chip-exit">{concepts.length}</span>
      </div>
      <div className="concepts-grid">
        {concepts.map((concept) => (
          <span key={concept} className="concept-chip">
            <span className="concept-chip-icon">
              {iconMap[concept] || "📌"}
            </span>
            {concept.replace(/_/g, " ")}
          </span>
        ))}
      </div>
    </div>
  );
}

export default ConceptsDetectedPanel;
