"""Báo cáo tổng hợp hằng ngày: gom dữ liệu + render ra HTML.

Dùng được 3 cách:
- Lệnh trong agent:   /daily_report
- Tool cho LLM gọi:   create_daily_report  (vd "tạo báo cáo hôm nay")
- CLI / hẹn giờ:      python -m tools.report [--open]

Render từ template templates/daily_report.html (sửa giao diện ở đó).
Xuất ra data/reports/<ngày>.html.
"""
from __future__ import annotations

import webbrowser
from datetime import datetime, time

from jinja2 import Environment, FileSystemLoader, select_autoescape

from config import BASE_DIR, DATA_DIR

from . import tool
from . import store

_WEEKDAYS = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]


def _today_bounds():
    """(bây giờ, đầu ngày, cuối ngày) theo giờ địa phương, dạng có timezone."""
    now = datetime.now().astimezone()
    start = datetime.combine(now.date(), time.min, tzinfo=now.tzinfo)
    end = datetime.combine(now.date(), time.max, tzinfo=now.tzinfo)
    return now, start, end


def _gather_events(start, end) -> list[dict]:
    """Sự kiện Calendar hôm nay. Trả [] nếu chưa đăng nhập Google."""
    try:
        from .google_auth import get_service
        res = get_service("calendar", "v3").events().list(
            calendarId="primary", timeMin=start.isoformat(), timeMax=end.isoformat(),
            singleEvents=True, orderBy="startTime",
        ).execute()
    except Exception as e:  # noqa: BLE001
        print(f"  [bỏ qua Calendar] {type(e).__name__}: {str(e)[:80]}")
        return []
    out = []
    for e in res.get("items", []):
        raw = e["start"].get("dateTime")
        out.append({
            "time": raw[11:16] if raw else "Cả ngày",
            "title": e.get("summary", "(không tên)"),
        })
    return out


def _gather_tasks(today_date) -> list[dict]:
    out = []
    for t in store.load("tasks", []):
        if t.get("done"):
            continue
        due = t.get("due", "")
        overdue = False
        try:  # nếu due bắt đầu bằng YYYY-MM-DD và đã qua -> quá hạn
            overdue = datetime.fromisoformat(due[:10]).date() < today_date
        except (ValueError, TypeError):
            pass
        out.append({"title": t["title"], "due": due, "overdue": overdue})
    return out


def _gather_emails(max_results: int = 8) -> list[dict]:
    try:
        from .google_auth import get_service
        svc = get_service("gmail", "v1")
        ids = svc.users().messages().list(
            userId="me", q="is:unread", maxResults=max_results
        ).execute().get("messages", [])
    except Exception as e:  # noqa: BLE001
        print(f"  [bỏ qua Gmail] {type(e).__name__}: {str(e)[:80]}")
        return []
    out = []
    for m in ids:
        full = svc.users().messages().get(
            userId="me", id=m["id"], format="metadata",
            metadataHeaders=["From", "Subject", "Date"],
        ).execute()
        h = {x["name"].lower(): x["value"] for x in full.get("payload", {}).get("headers", [])}
        out.append({
            "from": h.get("from", ""),
            "subject": h.get("subject", "(không tiêu đề)"),
            "date": h.get("date", ""),
        })
    return out


def _gather_memories() -> list[dict]:
    return [{"topic": m.get("topic", "chung"), "content": m["content"]}
            for m in store.load("memory", [])]


def build_report(open_browser: bool = False) -> str:
    """Gom dữ liệu, render template, ghi file HTML. Trả về đường dẫn file."""
    now, start, end = _today_bounds()
    events = _gather_events(start, end)
    tasks = _gather_tasks(now.date())
    emails = _gather_emails()
    memories = _gather_memories()

    env = Environment(
        loader=FileSystemLoader(str(BASE_DIR / "templates")),
        autoescape=select_autoescape(["html"]),
    )
    html = env.get_template("daily_report.html").render(
        date_str=now.strftime("%d/%m/%Y"),
        weekday=_WEEKDAYS[now.weekday()],
        generated_at=now.strftime("%H:%M %d/%m/%Y"),
        events=events, tasks=tasks, emails=emails, memories=memories,
        stats={"events": len(events), "tasks": len(tasks), "emails": len(emails)},
    )

    out_dir = DATA_DIR / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{now.strftime('%Y-%m-%d')}.html"
    out_path.write_text(html, encoding="utf-8")
    print(f"✓ Đã tạo báo cáo: {out_path}")
    print(f"  Lịch: {len(events)} · Việc: {len(tasks)} · Email chưa đọc: {len(emails)} · Ghi nhớ: {len(memories)}")
    if open_browser:
        webbrowser.open(out_path.as_uri())
    return str(out_path)


@tool(
    "Tạo báo cáo tổng hợp HÔM NAY (lịch, việc cần làm, email chưa đọc, ghi nhớ) ra file HTML. "
    "Dùng khi người dùng muốn xem tổng quan ngày hôm nay.",
    open_browser="True để mở báo cáo trong trình duyệt sau khi tạo. Mặc định true.",
)
def create_daily_report(open_browser: bool = True) -> str:
    path = build_report(open_browser=open_browser)
    return f"Đã tạo báo cáo tổng hợp hôm nay tại: {path}" + (
        " (đã mở trong trình duyệt)." if open_browser else "."
    )


if __name__ == "__main__":
    import io
    import sys

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    build_report(open_browser="--open" in sys.argv)
