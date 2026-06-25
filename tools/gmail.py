"""Tool Gmail: tìm/đọc email, tạo nháp, gửi mail.

Dùng OAuth qua google_auth. Gửi mail là hành động nhạy cảm — agent được
hướng dẫn (trong system prompt) phải hỏi xác nhận trước khi gửi.
"""
from __future__ import annotations

import base64
from email.message import EmailMessage

from . import tool
from .google_auth import get_service


def _svc():
    return get_service("gmail", "v1")


def _header(msg: dict, name: str) -> str:
    for h in msg.get("payload", {}).get("headers", []):
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


def _extract_body(payload: dict) -> str:
    """Lấy phần text/plain đầu tiên từ message payload."""
    if payload.get("mimeType") == "text/plain":
        data = payload.get("body", {}).get("data")
        if data:
            return base64.urlsafe_b64decode(data).decode("utf-8", "replace")
    for part in payload.get("parts", []) or []:
        text = _extract_body(part)
        if text:
            return text
    return ""


@tool(
    "Tìm/liệt kê email trong hộp thư. Trả về danh sách kèm id, người gửi, tiêu đề.",
    query="Cú pháp tìm kiếm Gmail, vd 'is:unread', 'from:sep@x.com', 'hóa đơn'. Bỏ trống = mới nhất.",
    max_results="Số email tối đa trả về (mặc định 10).",
)
def search_emails(query: str = "", max_results: int = 10) -> str:
    res = _svc().users().messages().list(
        userId="me", q=query, maxResults=max_results
    ).execute()
    ids = res.get("messages", [])
    if not ids:
        return "Không có email nào khớp."
    lines = []
    for m in ids:
        full = _svc().users().messages().get(
            userId="me", id=m["id"], format="metadata",
            metadataHeaders=["From", "Subject", "Date"],
        ).execute()
        lines.append(
            f"[{m['id']}] {_header(full,'From')} — {_header(full,'Subject') or '(không tiêu đề)'}"
            f" · {_header(full,'Date')}"
        )
    return "\n".join(lines)


@tool(
    "Đọc nội dung đầy đủ của một email theo id (lấy từ search_emails).",
    message_id="ID của email.",
)
def read_email(message_id: str) -> str:
    msg = _svc().users().messages().get(userId="me", id=message_id, format="full").execute()
    body = _extract_body(msg.get("payload", {})) or msg.get("snippet", "")
    return (
        f"Từ: {_header(msg,'From')}\n"
        f"Đến: {_header(msg,'To')}\n"
        f"Tiêu đề: {_header(msg,'Subject')}\n"
        f"Ngày: {_header(msg,'Date')}\n\n"
        f"{body.strip()}"
    )


def _build_raw(to: str, subject: str, body: str) -> dict:
    em = EmailMessage()
    em["To"] = to
    em["Subject"] = subject
    em.set_content(body)
    raw = base64.urlsafe_b64encode(em.as_bytes()).decode()
    return {"raw": raw}


@tool(
    "Tạo email NHÁP (chưa gửi) để người dùng xem lại. An toàn.",
    to="Địa chỉ người nhận.",
    subject="Tiêu đề.",
    body="Nội dung email.",
)
def create_draft(to: str, subject: str, body: str) -> str:
    draft = _svc().users().drafts().create(
        userId="me", body={"message": _build_raw(to, subject, body)}
    ).execute()
    return f"Đã tạo nháp gửi tới {to} (draft id: {draft['id']}). Người dùng có thể xem lại trong Gmail."


@tool(
    "GỬI email ngay tới người nhận. Hành động nhạy cảm — chỉ gửi sau khi người dùng xác nhận.",
    to="Địa chỉ người nhận.",
    subject="Tiêu đề.",
    body="Nội dung email.",
)
def send_email(to: str, subject: str, body: str) -> str:
    sent = _svc().users().messages().send(
        userId="me", body=_build_raw(to, subject, body)
    ).execute()
    return f"Đã gửi email tới {to} (id: {sent['id']})."
