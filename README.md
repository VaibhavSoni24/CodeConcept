# CodeConcept 🧠💻

**Adaptive AI Code Learning Diagnostic & Concept Correction Engine**

CodeConcept is an educational coding tool that goes beyond simple syntax checking and debugging. It analyzes student-written Python code to detect deep **conceptual misunderstandings**, identify **code smells**, compute **complexity metrics**, and trace **execution flow**. Instead of just giving the answer, it provides **progressive hints**, **refactoring suggestions**, and tracks a learner's mastery over time using a **skill graph**.

---

## 🚀 Features

### 1. Advanced Static Analysis
*   **Misconception Detection:** Identifies logical errors (e.g., off-by-one errors, mutable default arguments, float equality issues, shadowing built-ins) using raw Python AST traversal.
*   **Concept Detector:** Auto-detects programming constructs used in the code (loops, conditionals, comprehensions, recursion, etc.).
*   **Code Smell Analyzer:** Flags poor practices like deep nesting, large functions, long parameter lists, and unused variables.
*   **Complexity Metrics:** Calculates cyclomatic complexity, loop depth, and branch counts to evaluate code maintainability.

### 2. Behavioral Analysis
*   **Execution Tracer:** Runs student code in a sandboxed subprocess using `sys.settrace` to capture step-by-step execution states and variable values.
*   **Flow Graph Generator:** Parses the AST to build a Control Flow Graph (CFG) and automatically renders it as a Mermaid.js diagram.

### 3. AI-Powered Diagnostics & Learning
*   **AI Concept Correction:** Uses LLMs (OpenAI) to explain the *why* behind mistakes, generating progressive hints rather than giving away the solution.
*   **Refactoring Suggestions:** AI and rule-based suggestions to improve code quality without changing logic.
*   **Learning Skill Graph:** Tracks `correct_usage` and `total_usage` of concepts over time, visualizing mastery levels on a radar chart.

---

## 🛠️ Tech Stack

### Backend
*   **Framework:** FastAPI (Python)
*   **Database:** SQLite with SQLAlchemy ORM
*   **Analysis:** Python `ast` module, `sys.settrace` (for tracing), Subprocess (for sandboxing)
*   **AI Integration:** OpenAI API (`gpt-4o-mini` or similar)

### Frontend
*   **Framework:** React (Vite)
*   **Styling:** Custom CSS (Modern, dark-theme, glassmorphism UI)
*   **Visualizations:** 
    *   [Recharts](https://recharts.org/) for Skill Graph Radar Charts
    *   [Mermaid.js](https://mermaid.js.org/) for Control Flow Diagrams

---

## 📂 Project Structure

```text
CodeConcept/
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI application & API routes
│   │   ├── models.py                   # SQLAlchemy database models (User, Submission, ConceptSkill)
│   │   ├── database.py                 # SQLite DB connection setup
│   │   ├── data/
│   │   │   └── concept_rules.json      # Rules engine for 15+ misconceptions
│   │   ├── services/
│   │   │   ├── static_analyzer.py      # Base AST parsing
│   │   │   ├── misconception_detector.py # Logical AST rules detection
│   │   │   ├── smell_analyzer.py       # Code smell detection
│   │   │   ├── complexity_analyzer.py  # Cyclomatic complexity calculation
│   │   │   ├── concept_detector.py     # Used features detection
│   │   │   ├── execution_tracer.py     # Sandboxed step-by-step tracing
│   │   │   ├── flow_graph.py           # AST to Mermaid control flow graph
│   │   │   ├── profile_service.py      # Learning progress & skill tracking
│   │   │   └── diagnostic_ai.py        # OpenAI API integration & refactoring hints
│   └── requirements.txt
│
└── frontend/
    ├── src/
    │   ├── App.jsx                     # Main application layout & state
    │   ├── api.js                      # Axios API client
    │   ├── index.css                   # Global styles & UI components
    │   └── components/                 # UI Components (TabBar, Editor, Tracers, Charts, etc.)
    ├── package.json
    └── vite.config.js
```

---

## 💻 Installation & Setup

### Prerequisites
*   Node.js (v16+)
*   Python (3.9+)
*   OpenAI API Key (Optional, but required for AI hints)

### 1. Backend Setup

```bash
cd backend
python -m venv .venv
# Activate virtual environment
# Windows: .venv\Scripts\activate
# Mac/Linux: source .venv/bin/activate

pip install -r requirements.txt

# Set your OpenAI API key (optional)
# Windows: $env:OPENAI_API_KEY="your-key-here"
# Mac/Linux: export OPENAI_API_KEY="your-key-here"

# Start the FastAPI server
uvicorn app.main:app --reload --port 8000
```
*The backend will be available at `http://localhost:8000`. The DB will be automatically created on the first run.*

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```
*The frontend will be available at `http://localhost:5173`.*

---

## 🎮 How to Use

1. Open `http://localhost:5173` in your browser.
2. Click **"Create Learner"** to initialize a new user profile.
3. Write or paste Python code into the **Code Editor**.
   * *Try introducing a logical error like an off-by-one loop: `for i in range(len(arr)+1):`*
4. Click **"Analyze"**.
5. Explore the interactive tabs:
   * **Diagnosis:** See AI-driven explanations and progressive hints for any concepts missed.
   * **Code Quality:** Check for code smells, complexity metrics, and detected concepts.
   * **Trace & Flow:** Step through the code execution line-by-line and view the Mermaid control flow graph.
   * **Progress:** View your mastery across different Python concepts mapped on a dynamic radar chart.

---

*Built locally with AI assistance.*
