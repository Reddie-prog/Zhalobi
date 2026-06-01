"""Local dev runner: SQLite + serves frontend static files from FastAPI."""
import os, sys

# Set env vars BEFORE importing app modules
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./zhalobi.db")
os.environ.setdefault("SECRET_KEY", "local-dev-secret-key")
os.environ.setdefault("ESCALATION_HOURS", "72")

# Add backend to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from fastapi.staticfiles import StaticFiles
from app.main import app

# Mount frontend static files at "/" — API routes at /api/* take priority
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend")
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    print("\n🏗️  Жалоби ЖКХ — Local Dev Server")
    print("─" * 40)
    print("🌐  http://localhost:8000")
    print("📖  API docs: http://localhost:8000/docs")
    print("🔑  Admin: admin@zhalobi.ru / admin123")
    print("─" * 40 + "\n")
    uvicorn.run("local_main:app", host="0.0.0.0", port=8000, reload=True,
                reload_dirs=["backend", "frontend"])
