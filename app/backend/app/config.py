from pathlib import Path
import os

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


BASE_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BASE_DIR.parents[1]

if load_dotenv:
    load_dotenv(PROJECT_ROOT / ".env")
    load_dotenv(BASE_DIR / ".env")


def project_path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else PROJECT_ROOT / path


def comma_separated_values(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


DEFAULT_CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
]


DATABASE_PATH = project_path(os.getenv("DATABASE_PATH", BASE_DIR / "fashion.db"))
UPLOAD_DIR = project_path(os.getenv("UPLOAD_DIR", BASE_DIR / "uploads"))
CORS_ORIGINS = DEFAULT_CORS_ORIGINS + comma_separated_values(os.getenv("CORS_ORIGINS"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
