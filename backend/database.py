import os
import tempfile
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from backend.config import DATABASE_URL, BASE_DIR

db_url = os.getenv("DATABASE_URL")

if not db_url:
    if os.getenv("VERCEL"):
        temp_dir = tempfile.gettempdir()
        db_path = os.path.join(temp_dir, "talentmatch.db")
        db_url = f"sqlite:///{db_path}"
    else:
        db_url = DATABASE_URL

if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

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


