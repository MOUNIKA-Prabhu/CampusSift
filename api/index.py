import sys
import os
import traceback
from pathlib import Path
from fastapi import FastAPI

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

os.environ["VERCEL"] = "1"

app = FastAPI()

import_results = {}

def check_import(mod_name):
    try:
        __import__(mod_name)
        import_results[mod_name] = "SUCCESS"
    except Exception as e:
        import_results[mod_name] = f"FAILED: {type(e).__name__}: {str(e)}\n{traceback.format_exc()}"

check_import("backend.config")
check_import("backend.resume_parser")
check_import("backend.ranking_service")
check_import("backend.evaluation")
check_import("backend.nlp_llm_service")
check_import("backend.database")
check_import("backend.models")
check_import("backend.main")

@app.get("/api/diagnostic")
@app.get("/diagnostic")
def diagnostic():
    return import_results







