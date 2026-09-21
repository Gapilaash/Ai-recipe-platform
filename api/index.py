"""
Vercel entry point: exposes the FastAPI app from ../backend as a serverless function.
(Locally you still run:  cd backend && uvicorn main:app --reload)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from main import app  # noqa: E402,F401  (Vercel looks for a module-level `app`)
