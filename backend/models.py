import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from backend.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class JobDescription(Base):
    __tablename__ = "job_descriptions"

    id = Column(String, primary_key=True, default=generate_uuid)
    jobTitle = Column(String, nullable=False)
    company = Column(String, nullable=True)
    description = Column(Text, nullable=False)
    requiredSkills = Column(JSON, nullable=True)
    preferredSkills = Column(JSON, nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)

    sessions = relationship("RecruitmentSession", back_populates="job_description", cascade="all, delete-orphan")
    screening_results = relationship("ScreeningResult", back_populates="job_description", cascade="all, delete-orphan")

class RecruitmentSession(Base):
    __tablename__ = "recruitment_sessions"

    id = Column(String, primary_key=True, default=generate_uuid)
    jobDescriptionId = Column(String, ForeignKey("job_descriptions.id"), nullable=False)
    company = Column(String, nullable=True)
    sessionName = Column(String, nullable=False)
    mode = Column(String, default="persistent")  # "persistent" or "temporary"
    createdAt = Column(DateTime, default=datetime.utcnow)

    job_description = relationship("JobDescription", back_populates="sessions")
    candidates = relationship("Candidate", back_populates="recruitment_session", cascade="all, delete-orphan")
    screening_results = relationship("ScreeningResult", back_populates="recruitment_session", cascade="all, delete-orphan")

class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(String, primary_key=True, default=generate_uuid)
    sessionId = Column(String, ForeignKey("recruitment_sessions.id"), nullable=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    resumeFileName = Column(String, nullable=True)
    resumeText = Column(Text, nullable=True)
    education = Column(JSON, nullable=True)
    experience = Column(Float, default=0.0)
    extractedSkills = Column(JSON, nullable=True)
    projects = Column(JSON, nullable=True)
    certifications = Column(JSON, nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)

    recruitment_session = relationship("RecruitmentSession", back_populates="candidates")
    screening_results = relationship("ScreeningResult", back_populates="candidate", cascade="all, delete-orphan")

class ScreeningResult(Base):
    __tablename__ = "screening_results"

    id = Column(String, primary_key=True, default=generate_uuid)
    jobDescriptionId = Column(String, ForeignKey("job_descriptions.id"), nullable=False)
    sessionId = Column(String, ForeignKey("recruitment_sessions.id"), nullable=True)
    candidateId = Column(String, ForeignKey("candidates.id"), nullable=False)
    overallMatchScore = Column(Float, nullable=False)
    semanticSimilarityScore = Column(Float, nullable=False)
    skillMatchScore = Column(Float, nullable=False)
    educationScore = Column(Float, nullable=False)
    experienceScore = Column(Float, nullable=False)
    matchingSkills = Column(JSON, nullable=True)
    missingSkills = Column(JSON, nullable=True)
    explanation = Column(Text, nullable=True)
    rank = Column(Integer, nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)

    job_description = relationship("JobDescription", back_populates="screening_results")
    recruitment_session = relationship("RecruitmentSession", back_populates="screening_results")
    candidate = relationship("Candidate", back_populates="screening_results")

