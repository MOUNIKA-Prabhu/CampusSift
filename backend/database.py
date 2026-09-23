import os
import tempfile
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from backend.config import BASE_DIR

# 1. Check if user configured external DATABASE_URL (e.g. Postgres / Supabase)
env_db_url = os.getenv("DATABASE_URL", "")

if env_db_url and (env_db_url.startswith("postgres") or env_db_url.startswith("mysql")):
    db_url = env_db_url.replace("postgres://", "postgresql://", 1)
elif os.getenv("VERCEL") or os.getenv("VERCEL_ENV") or not os.access(str(BASE_DIR), os.W_OK):
    temp_dir = tempfile.gettempdir()
    db_path = os.path.join(temp_dir, "talentmatch.db")
    db_url = f"sqlite:///{db_path}"
else:
    db_path = BASE_DIR / "talentmatch.db"
    db_url = f"sqlite:///{db_path}"

connect_args = {}
if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(db_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"Warning: Database initialization notice: {e}")

def get_db():
    init_db()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



