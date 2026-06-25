"""Xác thực Google OAuth dùng chung cho Gmail & Calendar.

Lần đầu chạy sẽ mở trình duyệt để bạn cho phép, sau đó lưu token vào
token.json để các lần sau không hỏi lại (tự refresh khi hết hạn).

Nếu đổi SCOPES -> phải xoá token.json để xin lại quyền.
"""
from __future__ import annotations

from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config import BASE_DIR

# Quyền agent xin từ Google. Tối thiểu cho nhu cầu trợ lý cá nhân.
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",  # đọc/tìm mail
    "https://www.googleapis.com/auth/gmail.compose",   # tạo nháp
    "https://www.googleapis.com/auth/gmail.send",      # gửi mail
    "https://www.googleapis.com/auth/calendar.events",  # đọc/tạo/sửa/xoá sự kiện
]

_CREDENTIALS_FILE = BASE_DIR / "credentials.json"
_TOKEN_FILE = BASE_DIR / "token.json"

# Cache service đã build để khỏi tạo lại mỗi lần gọi tool.
_services: dict[str, object] = {}


def _get_credentials() -> Credentials:
    creds: Credentials | None = None
    if _TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(_TOKEN_FILE), SCOPES)
    if creds and creds.valid:
        return creds
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        if not _CREDENTIALS_FILE.exists():
            raise FileNotFoundError(
                "Thiếu credentials.json — tải từ Google Cloud Console (OAuth Desktop app) "
                "và đặt vào thư mục dự án."
            )
        flow = InstalledAppFlow.from_client_secrets_file(str(_CREDENTIALS_FILE), SCOPES)
        creds = flow.run_local_server(port=0)
    _TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
    return creds


def get_service(api: str, version: str):
    """Trả về Google API service (có cache). Vd get_service('gmail', 'v1')."""
    key = f"{api}:{version}"
    if key not in _services:
        _services[key] = build(api, version, credentials=_get_credentials(), cache_discovery=False)
    return _services[key]
