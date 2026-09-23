import sys
import os
from pathlib import Path

# Add project root directory to sys.path for Vercel serverless imports
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

os.environ["VERCEL"] = "1"

try:
    from backend.main import app
except Exception as e:
    import traceback
    err_msg = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    app = FastAPI()

    @app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
    def catch_all_error(path: str):
        return JSONResponse(
            status_code=500,
            content={"error": "Backend initialization exception", "detail": err_msg}
        )


try:
    from mangum import Mangum
    handler = Mangum(app, lifespan="off")
except Exception:
    handler = app


