import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
ISSUER = "tourshield"
AUDIENCE = "tourshield-api"
TOKEN_MINUTES = 15


def get_secret() -> str:
    value = os.getenv("JWT_SECRET", "")
    if len(value.encode()) < 32:
        raise RuntimeError("Configure JWT_SECRET com pelo menos 32 bytes aleatórios no .env")
    return value


def database_path() -> str:
    return os.getenv("DATABASE_PATH", str(ROOT / "tourshield.sqlite3"))
