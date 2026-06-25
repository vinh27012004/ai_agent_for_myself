"""Tool trí nhớ dài hạn: ghi nhớ thông tin về người dùng qua nhiều phiên.

Lưu vào data/memory.json dưới dạng danh sách các 'fact' có nhãn chủ đề.
Agent nên chủ động gọi remember() khi người dùng tiết lộ thông tin lâu dài
(sở thích, mục tiêu, người quen, thói quen...) và recall() khi cần ngữ cảnh.
"""
from __future__ import annotations

from datetime import datetime

from . import tool
from . import store

_NAME = "memory"


def _load() -> list[dict]:
    return store.load(_NAME, [])


def _save(items: list[dict]) -> None:
    store.save(_NAME, items)


@tool(
    "Ghi nhớ một thông tin lâu dài về người dùng để dùng ở các phiên sau.",
    content="Nội dung cần nhớ (một câu sự thật ngắn gọn).",
    topic="Chủ đề/nhãn để phân loại, ví dụ 'sở thích', 'công việc', 'sức khoẻ'.",
)
def remember(content: str, topic: str = "chung") -> str:
    items = _load()
    items.append(
        {
            "topic": topic,
            "content": content,
            "ts": datetime.now().isoformat(timespec="minutes"),
        }
    )
    _save(items)
    return f"Đã nhớ ({topic}): {content}"


@tool(
    "Tìm lại thông tin đã nhớ. Để trống query để xem toàn bộ.",
    query="Từ khoá tìm trong nội dung/chủ đề. Bỏ trống = tất cả.",
)
def recall(query: str = "") -> str:
    items = _load()
    if query:
        q = query.lower()
        items = [m for m in items if q in m["content"].lower() or q in m["topic"].lower()]
    if not items:
        return "Chưa có thông tin nào được ghi nhớ." if not query else f"Không tìm thấy gì cho '{query}'."
    return "\n".join(f"[{m['topic']}] {m['content']}" for m in items)


@tool("Quên (xoá) các thông tin đã nhớ khớp với từ khoá.", query="Từ khoá để xác định mục cần quên.")
def forget(query: str) -> str:
    items = _load()
    q = query.lower()
    keep = [m for m in items if q not in m["content"].lower() and q not in m["topic"].lower()]
    removed = len(items) - len(keep)
    _save(keep)
    return f"Đã quên {removed} mục khớp với '{query}'."
