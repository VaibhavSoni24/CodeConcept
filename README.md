# CodeConcept

CodeConcept is an AI-assisted learning platform that helps students understand conceptual mistakes in code, not just syntax errors. It combines runtime execution, static analysis, AST visualization, and guided feedback into one workflow.

## Highlights

- JWT-based authentication (register/login/current user).
- Multi-language code execution support for:
    - Python
    - JavaScript
    - C/C++ (via g++)
    - Java (via javac/java)
    - Go
    - Rust
- Deep conceptual analysis pipeline for Python submissions:
    - syntax + AST flags
    - misconception detection
    - code smell detection
    - complexity metrics
    - concept detection
    - flow graph generation
- AST graph endpoint for Python and supported Tree-sitter languages.
- AI-assisted diagnostics with fallback behavior when no AI key is configured.
- Learning profile and skill score tracking.
- Modern React frontend with Monaco editor and visual analysis panels.

## Architecture

### Backend

- Framework: FastAPI
- Database ORM: SQLAlchemy
- Validation: Pydantic
- Auth: JWT (`python-jose`) + bcrypt (`passlib`)
- Default DB: SQLite (`sqlite:///./codeconcept.db`)

### Frontend

- React + Vite
- Routing: React Router
- API client: Axios
- Editor: Monaco
- Charts/visuals: Recharts, React Flow

## Project Structure

```text
CodeConcept/
    backend/
        app/
            main.py
            auth_routes.py
            database.py
            models.py
            routes/
            schemas/
            services/
            data/
        requirements.txt
    frontend/
        src/
            App.jsx
            api.js
            components/
            pages/
        package.json
    README.md
```

## Prerequisites

- Python 3.10+
- Node.js 18+
- npm

Optional (for non-Python runtime execution):

- Node.js runtime (`node`) for JavaScript execution
- GCC/G++ for C/C++ execution
- JDK (`javac`, `java`) for Java execution
- Go toolchain (`go`) for Go execution
- Rust toolchain (`rustc`) for Rust execution

## Quick Start

### 1) Clone and enter project

```powershell
git clone <your-repo-url>
cd CodeConcept
```

### 2) Start backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Backend:

- API base: `http://localhost:8000`
- Interactive docs: `http://localhost:8000/docs`

### 3) Start frontend (new terminal)

```powershell
cd frontend
npm install
npm run dev
```

Frontend:

- App: `http://localhost:5173`

## Environment Variables

Backend reads environment variables at runtime (optionally from `.env`):

- `DATABASE_URL`
    - Default: `sqlite:///./codeconcept.db`
    - Set this for PostgreSQL or other SQLAlchemy-supported databases.

- `JWT_SECRET`
    - Default exists for local development.
    - Must be overridden in production.

- `INCEPTION_API_KEY`
    - Optional key used by AI diagnostic service.

- `INCEPTION_MODEL`
    - Optional model override for diagnostics.

Example `.env` (backend):

```env
DATABASE_URL=sqlite:///./codeconcept.db
JWT_SECRET=replace-with-a-strong-secret
INCEPTION_API_KEY=
INCEPTION_MODEL=mercury-2
```

## API Endpoints

### Public

- `GET /health`
- `POST /auth/register`
- `POST /auth/login`
- `POST /users` (legacy helper endpoint; can create user records without auth checks)

### Authenticated (Bearer token)

- `GET /auth/me`
- `POST /run-code`
- `POST /format-code`
- `POST /trace`
- `POST /submit-code`
- `POST /ast-graph`
- `GET /profiles/{user_id}`

Notes:

- `run-code` supports multiple languages as listed above.
- `submit-code` accepts language, but deep analysis is currently Python-first. Non-Python requests return limited analysis placeholders.
- `trace` currently uses Python execution tracing.

## Frontend Configuration

Frontend uses:

- `VITE_API_BASE` (optional)
    - Default: `http://localhost:8000`

Example `frontend/.env`:

```env
VITE_API_BASE=http://localhost:8000
```

## Typical Workflow

1. Register or login.
2. Open the Editor page.
3. Select language and write/upload code.
4. Click `Run` for runtime output.
5. Click `Analyze` for conceptual feedback, smells, complexity, and profile updates.
6. Explore AST/trace/flow/progress tabs.

## Development Commands

### Backend

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

Optional local syntax validation:

```powershell
cd backend
.\.venv\Scripts\python.exe -m compileall app
```

### Frontend

```powershell
cd frontend
npm run dev
npm run build
npm run preview
```

## Current Limitations

- Conceptual analysis quality is strongest for Python.
- Execution trace endpoint is Python-specific.
- Notes/activity routes are present but currently have placeholder implementations.
- Monaco editor component is currently configured with Python language mode; full per-language editor mode parity can be improved.
- Runtime execution uses local compilers/interpreters; deploy only in sandboxed environments for untrusted code.

## Security Notes

- Never use default JWT secrets in production.
- Restrict CORS origins in production.
- Run code execution in isolated containers/sandboxes for real-world deployment.

## License

No license file is currently defined in this repository.
