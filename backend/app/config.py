import os
from pathlib import Path
from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_DIR.parent
load_dotenv(BACKEND_DIR / ".env")
load_dotenv(PROJECT_ROOT / ".env")

API_KEY = os.getenv("NEBIUS_API_KEY", "").strip()
BASE_URL = os.getenv("NEBIUS_BASE_URL", "https://api.tokenfactory.nebius.com/v1/").strip()
MODEL_ID = os.getenv("NEBIUS_MODEL", "").strip()
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "").strip()
DATA_DIR = Path(os.getenv("AETHERCODE_DATA_DIR", str(BACKEND_DIR / "data"))).resolve()
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "25"))
MAX_FILES = int(os.getenv("MAX_FILES", "500"))
MAX_FILE_BYTES = int(os.getenv("MAX_FILE_BYTES", "200000"))
MAX_CONTEXT_CHARS = int(os.getenv("MAX_CONTEXT_CHARS", "80000"))
MAX_AGENT_RETRIES = int(os.getenv("MAX_AGENT_RETRIES", "2"))
SANDBOX_IMAGE = os.getenv("SANDBOX_IMAGE", "python:3.12-slim")
IGNORED_DIRS = {
    ".git", ".hg", ".svn", ".venv", "venv", "node_modules",
    "__pycache__", ".pytest_cache", ".mypy_cache", ".next",
    "dist", "build", "coverage", ".idea", ".vscode"
}
IGNORED_NAMES = {
    ".env", ".env.local", ".env.production", "id_rsa", "id_ed25519",
    "credentials.json", "secrets.json"
}
ALLOWED_TEXT_SUFFIXES = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".html", ".css", ".scss",
    ".json", ".md", ".txt", ".yml", ".yaml", ".toml", ".ini", ".cfg",
    ".sh", ".bat", ".ps1", ".sql", ".xml", ".java", ".c", ".h",
    ".cpp", ".hpp", ".go", ".rs", ".php", ".rb", ".swift", ".kt"
}
DATA_DIR.mkdir(parents=True, exist_ok=True)
