import os

from dotenv import load_dotenv

load_dotenv()


def _as_bool(value: str) -> bool:
    return value.strip().lower() in ("1", "true", "yes", "on")


DATABASE_URI = os.getenv("DATABASE_URI", "sqlite:///cascade_cleanup.db")
ENABLE_SOFT_DELETE = _as_bool(os.getenv("ENABLE_SOFT_DELETE", "true"))
SOFT_DELETE_RETENTION_DAYS = int(os.getenv("SOFT_DELETE_RETENTION_DAYS", "30"))
SQL_ECHO = _as_bool(os.getenv("SQL_ECHO", "false"))
