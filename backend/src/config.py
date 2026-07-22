import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
STORAGE_DIR = Path(os.environ.get("STORAGE_DIR") or (BASE_DIR / "storage" / "files"))
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

DB_URL = (
    f"postgresql+asyncpg://{os.environ.get('POSTGRES_USER')}:"
    f"{os.environ.get('POSTGRES_PASSWORD')}@{os.environ.get('POSTGRES_HOST')}:"
    f"{os.environ.get('PGPORT')}/{os.environ.get('POSTGRES_DB')}"
)

REDIS_URL = os.environ.get("REDIS_URL", "redis://backend-redis:6379/0")

MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024
MAX_TITLE_LENGTH = 255
