import { useEffect, useRef } from "react";

function FlowGraphPanel({ flowGraph }) {
  const containerRef = useRef(null);

  useEffect(() => {
    if (!flowGraph?.mermaid || !containerRef.current) return;

    // Dynamically load mermaid from CDN if not already loaded
    const renderChart = async () => {
      if (!window.mermaid) {
        const script = document.createElement("script");
        script.src =
          "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js";
        script.onload = () => {
          window.mermaid.initialize({
            startOnLoad: false,
            theme: "dark",
            themeVariables: {
              primaryColor: "#6366f1",
              primaryTextColor: "#f1f5f9",
              primaryBorderColor: "#4f46e5",
              lineColor: "#64748b",
              secondaryColor: "#1e293b",
              tertiaryColor: "#0f172a",
            },
          });
          doRender();
        };
        document.head.appendChild(script);
      } else {
        doRender();
      }
    };

    const doRender = async () => {
      try {
        const id = `mermaid-${Date.now()}`;
        const { svg } = await window.mermaid.render(id, flowGraph.mermaid);
        if (containerRef.current) {
          containerRef.current.innerHTML = svg;
        }
      } catch {
        if (containerRef.current) {
          containerRef.current.innerHTML =
            '<p style="color: var(--text-muted); font-style: italic;">Could not render flow graph.</p>';
        }
      }
    };

    renderChart();
  }, [flowGraph?.mermaid]);

  if (!flowGraph || !flowGraph.mermaid) {
    return (
      <div className="card card-glow">
        <div className="card-header">
          <h2>
            <span className="card-icon purple">🗺️</span>
            Control Flow
          </h2>
        </div>
        <p className="feedback-empty">
          Submit code to see the control flow graph.
        </p>
      </div>
    );
  }

  return (
    <div className="card card-glow fade-in">
      <div className="card-header">
        <h2>
          <span className="card-icon purple">🗺️</span>
          Control Flow
        </h2>
        <span className="chip chip-exit">
          {flowGraph.nodes?.length || 0} nodes
        </span>
      </div>
      <div className="flow-graph-container" ref={containerRef}>
        <p className="feedback-empty">Loading diagram…</p>
      </div>
    </div>
  );
}

export default FlowGraphPanel;
