import sys
import os
from pathlib import Path

# Add project root directory to sys.path for Vercel serverless imports
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

os.environ["VERCEL"] = "1"

from backend.main import app



