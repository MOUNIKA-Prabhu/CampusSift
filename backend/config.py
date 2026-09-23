import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env if present
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# API Keys (Loaded strictly from env, never hardcoded)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Database Configuration (Supports PostgreSQL / Supabase via env var, defaults to SQLite)
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'talentmatch.db'}")

# Weight factors for overall match score calculation
WEIGHT_SEMANTIC = 0.50
WEIGHT_SKILLS = 0.35
WEIGHT_QUALIFICATIONS = 0.15

# Directories
SAMPLE_DATA_DIR = BASE_DIR / "sample_data"
SAMPLE_RESUMES_DIR = SAMPLE_DATA_DIR / "sample_resumes"
SAMPLE_JDS_DIR = SAMPLE_DATA_DIR / "job_descriptions"
EVALUATION_DATASET_PATH = SAMPLE_DATA_DIR / "evaluation_dataset.json"

# List of common tech skills for robust regex fallback extraction
SKILL_TAXONOMY = [
    "Python", "Java", "C++", "C#", "JavaScript", "TypeScript", "HTML", "CSS", "SQL", "NoSQL",
    "React", "Angular", "Vue", "Node.js", "Express", "Django", "Flask", "FastAPI", "Spring Boot",
    "Machine Learning", "Deep Learning", "NLP", "Natural Language Processing", "Computer Vision",
    "TensorFlow", "PyTorch", "Scikit-Learn", "Pandas", "NumPy", "Keras", "OpenCV",
    "Docker", "Kubernetes", "AWS", "Azure", "GCP", "DevOps", "CI/CD", "Git", "GitHub",
    "REST API", "GraphQL", "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch",
    "Data Analysis", "Statistics", "Power BI", "Tableau", "Agile", "Scrum", "Linux"
]
