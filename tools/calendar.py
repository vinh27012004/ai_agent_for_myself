"""Tool Google Calendar: xem, tạo, sửa, xoá sự kiện.

Thời gian dùng định dạng ISO 8601, vd '2026-06-30T09:00:00'. Nếu không kèm
offset, coi như giờ địa phương của lịch. Xoá sự kiện là hành động nhạy cảm —
agent được hướng dẫn hỏi xác nhận trước.
"""
from __future__ import annotations

from datetime import datetime, timezone

from . import tool
from .google_auth import get_service


def _svc():
    return get_service("calendar", "v3")


@tool(
    "Liệt kê sự kiện sắp tới trên lịch chính.",
    max_results="Số sự kiện tối đa (mặc định 10).",
    time_min="Mốc bắt đầu ISO 8601 (vd '2026-06-25T00:00:00'). Bỏ trống = từ bây giờ.",
)
def list_events(max_results: int = 10, time_min: str = "") -> str:
    tmin = time_min or datetime.now(timezone.utc).isoformat()
    res = _svc().events().list(
        calendarId="primary", timeMin=tmin, maxResults=max_results,
        singleEvents=True, orderBy="startTime",
    ).execute()
    items = res.get("items", [])
    if not items:
        return "Không có sự kiện nào sắp tới."
    lines = []
    for e in items:
        start = e["start"].get("dateTime", e["start"].get("date", ""))
        lines.append(f"[{e['id']}] {start} — {e.get('summary', '(không tên)')}")
    return "\n".join(lines)


@tool(
    "Tạo sự kiện mới trên lịch.",
    summary="Tên/tiêu đề sự kiện.",
    start="Thời gian bắt đầu ISO 8601, vd '2026-06-30T09:00:00'.",
    end="Thời gian kết thúc ISO 8601. Bỏ trống = +1 giờ sau start.",
    description="Mô tả thêm (tuỳ chọn).",
)
def create_event(summary: str, start: str, end: str = "", description: str = "") -> str:
    body = {
        "summary": summary,
        "description": description,
        "start": {"dateTime": start},
        "end": {"dateTime": end or start},
    }
    if not end:
        # +1 giờ nếu không cho end
        try:
            dt = datetime.fromisoformat(start)
            body["end"] = {"dateTime": dt.replace(hour=dt.hour + 1).isoformat()}
        except ValueError:
            body["end"] = {"dateTime": start}
    ev = _svc().events().insert(calendarId="primary", body=body).execute()
    return f"Đã tạo sự kiện '{summary}' lúc {start} (id: {ev['id']}). Link: {ev.get('htmlLink','')}"


@tool(
    "Cập nhật một sự kiện (chỉ sửa trường được truyền).",
    event_id="ID sự kiện (lấy từ list_events).",
    summary="Tiêu đề mới (bỏ trống = giữ nguyên).",
    start="Bắt đầu mới ISO 8601 (bỏ trống = giữ nguyên).",
    end="Kết thúc mới ISO 8601 (bỏ trống = giữ nguyên).",
)
def update_event(event_id: str, summary: str = "", start: str = "", end: str = "") -> str:
    ev = _svc().events().get(calendarId="primary", eventId=event_id).execute()
    if summary:
        ev["summary"] = summary
    if start:
        ev["start"] = {"dateTime": start}
    if end:
        ev["end"] = {"dateTime": end}
    updated = _svc().events().update(calendarId="primary", eventId=event_id, body=ev).execute()
    return f"Đã cập nhật sự kiện '{updated.get('summary')}' (id: {event_id})."


@tool(
    "XOÁ một sự kiện khỏi lịch. Nhạy cảm — chỉ xoá sau khi người dùng xác nhận.",
    event_id="ID sự kiện cần xoá.",
)
def delete_event(event_id: str) -> str:
    _svc().events().delete(calendarId="primary", eventId=event_id).execute()
    return f"Đã xoá sự kiện id: {event_id}."
