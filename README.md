# CodeConcept

CodeConcept is an educational coding analysis platform that helps learners understand conceptual mistakes in code, not just syntax errors.

Current status:
- Authentication is enabled (register/login with JWT).
- Code execution, static analysis, and tracing are currently Python-focused.
- The platform provides hints, explanation, refactoring suggestions, and learning progress views.

## Core Features

- Concept-aware diagnostics from AST-based analysis.
- Misconception detection (examples: off-by-one ranges, mutable defaults, shadowed built-ins).
- Code smell checks (deep nesting, large functions, long parameter lists, unused variables).
- Complexity metrics (cyclomatic complexity, loop depth, branch count, recursion indicator).
- Step-by-step execution tracing using a sandboxed subprocess.
- Control flow graph generation (Mermaid format).
- AI-assisted explanation and hints with rule-based fallback.
- Learner profile and skill progression tracking over time.

## Tech Stack

Backend:
- FastAPI
- SQLAlchemy
- SQLite by default (configurable via environment)
- Pydantic
- JWT auth (python-jose)

Frontend:
- React + Vite
- Axios
- Monaco editor
- Recharts
- Tailwind toolchain (used by build pipeline)

## Repository Structure

```text
CodeConcept/
    backend/
        app/
            main.py
            auth_routes.py
            models.py
            database.py
            data/
                concept_rules.json
            schemas/
            services/
        requirements.txt
    frontend/
        src/
            App.jsx
            api.js
            index.css
            components/
        package.json
```

## Prerequisites

- Python 3.9+
- Node.js 18+
- npm

## Quick Start

### 1) Backend

From project root:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Backend URL:
- http://localhost:8000

### 2) Frontend

Open a second terminal from project root:

```powershell
cd frontend
npm install
npm run dev
```

Frontend URL:
- http://localhost:5173

## Environment Variables

Backend reads environment variables from runtime environment (and optional .env):

- JWT_SECRET
    - Secret for signing JWT tokens.
    - Default exists for local development but should be overridden in production.

- DATABASE_URL
    - Optional database connection string.
    - If unset, the app uses local SQLite defaults.

- INCEPTION_API_KEY
    - Optional key for AI diagnostics provider.
    - If unset, diagnostics fall back to rule-based responses.

- INCEPTION_MODEL
    - Optional model name override.
    - Default: mercury-2

## Main API Endpoints

Auth:
- POST /auth/register
- POST /auth/login
- GET /auth/me

App:
- GET /health
- POST /run-code
- POST /trace
- POST /submit-code
- GET /profiles/{user_id}

Notes:
- Most app endpoints require Bearer auth.
- /submit-code currently enforces language=python.

## Typical User Flow

1. Register or log in from the UI.
2. Paste Python code in the editor.
3. Click Run to execute code safely.
4. Click Analyze to get:
     - diagnosis and hints
     - smell and complexity insights
     - trace and flow visualization
     - profile updates

## Development Notes

- Backend auto-creates database tables on startup.
- Frontend build command:

```powershell
cd frontend
npm run build
```

- Backend syntax check:

```powershell
cd backend
.\.venv\Scripts\python.exe -m compileall app
```

## Current Limitations

- Analysis and execution are currently Python-only in the API flow.
- Trace engine is Python-specific.
- Multi-language support can be added incrementally by extending payload validation, execution runner, and frontend language controls.

## License

No license file is currently defined in this repository.
