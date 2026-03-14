from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from .database import Base, engine
from .models import User, Submission, ConceptError
from .auth_routes import router as auth_router

# Import routers
from .routes import code_routes, profile_routes, analysis_routes, activity_routes, notes_routes, knowledge_routes

Base.metadata.create_all(bind=engine)

app = FastAPI(title="CodeConcept MVP", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173", "http://127.0.0.1:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(profile_routes.router)
app.include_router(code_routes.router)
app.include_router(analysis_routes.router)
app.include_router(activity_routes.router)
app.include_router(notes_routes.router)
app.include_router(knowledge_routes.router)

@app.get("/health")
def health_check():
    return {"status": "ok"}
