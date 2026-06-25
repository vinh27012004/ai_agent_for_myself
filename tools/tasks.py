"""Tool quản lý công việc & nhắc nhở (lưu vào data/tasks.json)."""
from __future__ import annotations

from datetime import datetime

from . import tool
from . import store

_NAME = "tasks"


def _load() -> list[dict]:
    return store.load(_NAME, [])


def _save(items: list[dict]) -> None:
    store.save(_NAME, items)


def _next_id(items: list[dict]) -> int:
    return (max((t["id"] for t in items), default=0)) + 1


@tool(
    "Thêm một công việc/nhắc nhở mới vào danh sách.",
    title="Nội dung công việc",
    due="Hạn (chuỗi tự do, ví dụ '2026-06-30 09:00' hoặc 'ngày mai'). Có thể bỏ trống.",
)
def add_task(title: str, due: str = "") -> str:
    items = _load()
    task = {
        "id": _next_id(items),
        "title": title,
        "due": due,
        "done": False,
        "created": datetime.now().isoformat(timespec="minutes"),
    }
    items.append(task)
    _save(items)
    return f"Đã thêm task #{task['id']}: {title}" + (f" (hạn: {due})" if due else "")


@tool(
    "Liệt kê công việc. include_done=true để xem cả việc đã xong.",
    include_done="True để hiện cả việc đã hoàn thành.",
)
def list_tasks(include_done: bool = False) -> str:
    items = _load()
    if not include_done:
        items = [t for t in items if not t["done"]]
    if not items:
        return "Không có công việc nào."
    lines = []
    for t in items:
        mark = "✓" if t["done"] else "○"
        due = f" — hạn: {t['due']}" if t["due"] else ""
        lines.append(f"{mark} #{t['id']} {t['title']}{due}")
    return "\n".join(lines)


@tool("Đánh dấu một công việc là đã hoàn thành.", task_id="ID của công việc.")
def complete_task(task_id: int) -> str:
    items = _load()
    for t in items:
        if t["id"] == task_id:
            t["done"] = True
            _save(items)
            return f"Đã hoàn thành task #{task_id}: {t['title']}"
    return f"Không tìm thấy task #{task_id}."


@tool("Xoá một công việc khỏi danh sách.", task_id="ID của công việc.")
def delete_task(task_id: int) -> str:
    items = _load()
    new = [t for t in items if t["id"] != task_id]
    if len(new) == len(items):
        return f"Không tìm thấy task #{task_id}."
    _save(new)
    return f"Đã xoá task #{task_id}."
