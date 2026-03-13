# CodeConcept Backend (FastAPI)

## Run

1. Create environment and install dependencies.

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Start API.

```powershell
uvicorn app.main:app --reload --port 8000
```

3. Create a demo user.

```powershell
curl -X POST http://localhost:8000/users -H "Content-Type: application/json" -d '{"name":"Student One","email":"student1@example.com","level":"beginner"}'
```

4. Submit code.

```powershell
curl -X POST http://localhost:8000/submit-code -H "Content-Type: application/json" -d '{"user_id":1,"language":"python","code":"for i in range(10)\n    print(i)"}'
```

## Notes

- `DATABASE_URL` defaults to SQLite for quick setup. Use PostgreSQL by setting `DATABASE_URL`.
- Optional LLM diagnostics enabled with `OPENAI_API_KEY`.
