import os

from fastapi.templating import Jinja2Templates
from load_dotenv import load_dotenv

load_dotenv()

CORS_ORIGINS = ["*"]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ["*"]
CORS_ALLOW_HEADERS = ["*"]

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5434")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
print(DB_URL)
ECHO_SQL: bool = False

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "cherry4xo")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "25612812")
MINIO_BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME", "main")


templates = Jinja2Templates(directory="templates")