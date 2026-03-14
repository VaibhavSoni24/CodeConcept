from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(120), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=True)
    level = Column(String(50), default="beginner")
    credits = Column(Integer, default=100)
    created_at = Column(DateTime, default=datetime.utcnow)

    submissions = relationship("Submission", back_populates="user", cascade="all, delete")
    profiles = relationship("LearningProfile", back_populates="user", cascade="all, delete")


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    code = Column(Text, nullable=False)
    language = Column(String(20), default="python")
    timestamp = Column(DateTime, default=datetime.utcnow)
    result = Column(Text, nullable=False)
    analysis_result = Column(JSON, nullable=True)

    user = relationship("User", back_populates="submissions")
    concept_errors = relationship("ConceptError", back_populates="submission", cascade="all, delete")


class ConceptError(Base):
    __tablename__ = "concept_errors"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"), nullable=False)
    concept = Column(String(120), nullable=False)
    error_type = Column(String(120), nullable=False)
    severity = Column(String(20), default="medium")

    submission = relationship("Submission", back_populates="concept_errors")


class LearningProfile(Base):
    __tablename__ = "learning_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    concept = Column(String(120), nullable=False)
    mistake_count = Column(Integer, default=0)
    mastery_level = Column(String(20), default="beginner")
    last_seen = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="profiles")


class ConceptSkill(Base):
    __tablename__ = "concept_skills"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    concept = Column(String(120), nullable=False)
    language = Column(String, default="python", server_default="python")
    correct_usage = Column(Integer, default=0)
    total_usage = Column(Integer, default=0)
    score = Column(Integer, default=0)  # stored as int 0-100 for simplicity
    last_updated = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")


class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    analysis_id = Column(Integer, ForeignKey("submissions.id"), nullable=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    submission = relationship("Submission")
