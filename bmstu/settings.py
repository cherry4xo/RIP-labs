import os

from fastapi.templating import Jinja2Templates
import load_dotenv

CORS_ORIGINS = ["*"]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ["*"]
CORS_ALLOW_HEADERS = ["*"]

templates = Jinja2Templates(directory="templates")