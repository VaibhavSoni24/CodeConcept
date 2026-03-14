import React, { useEffect, useRef } from 'react';
import { BookOpen, Code, Zap, Target } from 'lucide-react';
import mermaid from 'mermaid';

function Mermaid({ chart }) {
  const ref = useRef(null);
  useEffect(() => {
    mermaid.initialize({ startOnLoad: true, theme: 'dark' });
    if (ref.current) {
      mermaid.contentLoaded();
    }
  }, [chart]);
  
  return (
    <div className="mermaid flex justify-center w-full overflow-x-auto" ref={ref}>
      {chart}
    </div>
  );
}

const diagram = `
graph TD
A[User Writes Code] --> B[Code Submitted]
B --> C[Execution Sandbox]
C --> D[AST Parser]
D --> E[Concept Analysis Engine]
E --> F[Misconception Detection]
F --> G[Code Quality Analyzer]
G --> H[Complexity Analyzer]
H --> I[AI Diagnostic Engine]
I --> J[Visualization Engine]
J --> K[Learning Dashboard]
K --> L[Skill Graph + Feedback]
`;

function About() {
  return (
    <div className="flex flex-col h-full overflow-y-auto w-full p-8 bg-[var(--bg-primary)]">
      <div className="max-w-4xl mx-auto w-full slide-up">
        <header className="mb-8">
          <h1 className="text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-indigo-500 mb-4">
            About CodeConcept
          </h1>
          <p className="text-[var(--text-secondary)] text-lg leading-relaxed">
            CodeConcept is an adaptive educational code analysis platform designed to focus on deep code reasoning, behavioral analysis, and conceptual mastery rather than simply catching syntax errors.
          </p>
        </header>

        <section className="card p-8 mb-8">
          <h2 className="text-2xl font-bold text-[var(--text-primary)] mb-6 flex items-center gap-2">
            <Target className="text-indigo-500" />
            Our Methodology
          </h2>
          <p className="text-[var(--text-secondary)] leading-relaxed mb-4">
            Traditional IDEs and linters tell you <em>where</em> your code broke. CodeConcept attempts to tell you <em>why</em> it broke conceptually. We track how you construct loops, handle variables, and structure logic across multiple languages.
          </p>
          <ul className="list-disc pl-5 space-y-2 text-[var(--text-secondary)]">
            <li><strong>Abstract Syntax Tree (AST) Analysis:</strong> We extract and normalize the structural layout of your code using tree-sitter to identify anti-patterns.</li>
            <li><strong>Execution Tracing:</strong> (For Python) We step through execution to show variable mutation state frame-by-frame.</li>
            <li><strong>Concept Mapping:</strong> Every mistake is categorized into foundational computer science concepts (e.g., "State Mutation", "Loop Invariants").</li>
            <li><strong>Adaptive Learning:</strong> The platform tracks your confidence scores across concepts, offering targeted feedback and YouTube resource recommendations when you struggle.</li>
          </ul>
        </section>

        <section className="card p-8 mb-8">
          <h2 className="text-2xl font-bold text-[var(--text-primary)] mb-6">System Workflow</h2>
          <div className="bg-[var(--bg-secondary)] p-4 rounded-xl border border-[var(--border)] overflow-x-auto">
             <Mermaid chart={diagram} />
          </div>
        </section>

        <section className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div className="card p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="px-3 py-2 bg-blue-500/10 rounded-lg"><Code className="text-blue-500" /></div>
              <h3 className="text-xl font-bold border-none text-[var(--text-primary)]">Multi-Language</h3>
            </div>
            <p className="text-[var(--text-secondary)] text-sm leading-relaxed">
              Support for Python, JavaScript, C++, Java, Go, and Rust. AST rules and compilation flows are unified under a single architecture.
            </p>
          </div>
          
          <div className="card p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="px-3 py-2 bg-amber-500/10 rounded-lg"><Zap className="text-amber-500" /></div>
              <h3 className="text-xl font-bold border-none text-[var(--text-primary)]">AI Fallback Engine</h3>
            </div>
            <p className="text-[var(--text-secondary)] text-sm leading-relaxed">
              When our static deterministic rules do not catch an error, the code is passed to an AI LLM (using the Inception API / Mercury-2 model) structured to return strictly typed diagnostic JSON.
            </p>
          </div>
        </section>
      </div>
    </div>
  );
}

export default About;
