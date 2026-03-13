# CodeConcept MVP

Adaptive AI Code Learning Diagnostic & Concept Correction Engine (Python-first MVP).

## What this MVP does

- Accepts Python code submissions.
- Performs syntax and AST concept analysis.
- Maps mistakes to learning concepts.
- Produces progressive hints and explanations.
- Tracks recurring concept mistakes per learner.

## Architecture

- Frontend: React + Monaco + Tailwind (`frontend`)
- Backend: FastAPI + SQLAlchemy (`backend`)
- Analysis: Python AST custom rules
- AI Layer: OpenAI API optional fallback
- Data: SQLite default, PostgreSQL-compatible via `DATABASE_URL`

## Quick Start

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Set frontend API base URL if needed:

```powershell
$env:VITE_API_BASE="http://localhost:8000"
```

## Key Endpoints

- `POST /users`
- `POST /run-code`
- `POST /submit-code`
- `GET /profiles/{user_id}`

## Example Submit Payload

```json
{
  "user_id": 1,
  "language": "python",
  "code": "for i in range(10)\n    print(i)"
}
```
