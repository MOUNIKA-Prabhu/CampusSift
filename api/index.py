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

@app.get("/api/diagnostic")
@app.get("/diagnostic")
def diagnostic():
    import_results = {}

    def check_import(mod_name):
        try:
            __import__(mod_name)
            import_results[mod_name] = "SUCCESS"
        except Exception as e:
            import_results[mod_name] = f"FAILED: {type(e).__name__}: {str(e)}\n{traceback.format_exc()}"

    mods = [
        "backend.config",
        "backend.resume_parser",
        "backend.ranking_service",
        "backend.evaluation",
        "backend.nlp_llm_service",
        "backend.database",
        "backend.models",
        "backend.main"
    ]
    for mod in mods:
        check_import(mod)

    return import_results








