import { useState } from "react";

function ExecutionTracePanel({ trace }) {
  const [currentStep, setCurrentStep] = useState(0);

  if (trace?.notAvailable) {
    return (
      <div className="card card-glow">
        <div className="card-header">
          <h2>
            <span className="card-icon green">🔍</span>
            Execution Trace
          </h2>
        </div>
        <p className="feedback-empty">
          Tracing is currently only supported for Python.
        </p>
      </div>
    );
  }

  if (!trace || trace.length === 0) {
    return (
      <div className="card card-glow">
        <div className="card-header">
          <h2>
            <span className="card-icon green">🔍</span>
            Execution Trace
          </h2>
        </div>
        <p className="feedback-empty">
          Submit code to see step-by-step execution.
        </p>
      </div>
    );
  }

  const hasError = trace.some(
    (step) => step.line === -1 && step.variables?.__error__
  );

  const validSteps = trace.filter((step) => step.line !== -1);
  const errorStep = trace.find((step) => step.line === -1);

  const step = validSteps[currentStep] || null;

  return (
    <div className="card card-glow fade-in">
      <div className="card-header">
        <h2>
          <span className="card-icon green">🔍</span>
          Execution Trace
        </h2>
        <span className="chip chip-exit">
          {validSteps.length} steps
        </span>
      </div>

      {hasError && errorStep && (
        <div className="trace-error">
          ⚠ {errorStep.variables.__error__}
        </div>
      )}

      {validSteps.length > 0 && (
        <>
          <div className="trace-controls">
            <button
              className="btn btn-trace"
              disabled={currentStep === 0}
              onClick={() => setCurrentStep((s) => s - 1)}
            >
              ◀ Prev
            </button>
            <span className="trace-step-label">
              Step {currentStep + 1} / {validSteps.length}
            </span>
            <button
              className="btn btn-trace"
              disabled={currentStep >= validSteps.length - 1}
              onClick={() => setCurrentStep((s) => s + 1)}
            >
              Next ▶
            </button>
          </div>

          {step && (
            <div className="trace-snapshot">
              <div className="trace-line-badge">
                Line {step.line}
              </div>
              <table className="trace-table">
                <thead>
                  <tr>
                    <th>Variable</th>
                    <th>Value</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(step.variables).map(([key, val]) => (
                    <tr key={key}>
                      <td className="trace-var-name">{key}</td>
                      <td className="trace-var-value">
                        {typeof val === "object"
                          ? JSON.stringify(val)
                          : String(val)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default ExecutionTracePanel;
