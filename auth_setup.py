"""Chạy một lần để đăng nhập Google (Gmail + Calendar) và tạo token.json.

    python auth_setup.py

Chạy lại nếu đổi quyền (SCOPES) hoặc token bị thu hồi. Xoá token.json để đăng
nhập lại từ đầu.
"""
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from tools.google_auth import get_service

print("Đang mở trình duyệt để đăng nhập Google...")
gmail = get_service("gmail", "v1")
profile = gmail.users().getProfile(userId="me").execute()
print(f"✓ Gmail OK — đăng nhập với: {profile.get('emailAddress')}")

from datetime import datetime, timezone

cal = get_service("calendar", "v3")
# Dùng events().list trên lịch primary — khớp đúng scope calendar.events.
cal.events().list(
    calendarId="primary", maxResults=1,
    timeMin=datetime.now(timezone.utc).isoformat(),
).execute()
print("✓ Calendar OK — token đã lưu vào token.json.")
print("Xong! Giờ chạy: python agent.py")
