"""Cấu hình tập trung, đọc từ .env (hoặc biến môi trường)."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

BASE_URL = os.getenv("AGENT_BASE_URL", "http://localhost:20128/v1")
API_KEY = os.getenv("AGENT_API_KEY", "")
MODEL = os.getenv("AGENT_MODEL", "CLine")

DATA_DIR = BASE_DIR / os.getenv("AGENT_DATA_DIR", "data")
DATA_DIR.mkdir(parents=True, exist_ok=True)
