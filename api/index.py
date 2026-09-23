import sys
import os
from pathlib import Path
from fastapi import FastAPI

app = FastAPI()

@app.get("/api/health")
def health():
    return {"status": "healthy", "message": "Vercel Python serverless engine is operating normally"}




