"""Tool làm việc với file & thư mục cục bộ.

- Đọc: list_dir, read_file (trả nội dung cho LLM xử lý).
- Ghi/sắp xếp: create_dir, move_file (có guardrail, không ghi đè mặc định).
"""
from __future__ import annotations

import shutil
from pathlib import Path

from . import tool

# Giới hạn an toàn để không nhồi quá nhiều token vào ngữ cảnh.
_MAX_CHARS = 20_000


@tool(
    "Liệt kê file và thư mục con trong một thư mục.",
    path="Đường dẫn thư mục. Mặc định thư mục hiện tại.",
)
def list_dir(path: str = ".") -> str:
    p = Path(path).expanduser()
    if not p.is_dir():
        return f"Không phải thư mục: {path}"
    entries = sorted(p.iterdir(), key=lambda e: (e.is_file(), e.name.lower()))
    lines = [("📁 " if e.is_dir() else "📄 ") + e.name for e in entries]
    return "\n".join(lines) if lines else "(thư mục rỗng)"


@tool(
    "Đọc nội dung văn bản của một file (txt, md, code, csv...).",
    path="Đường dẫn file cần đọc.",
)
def read_file(path: str) -> str:
    p = Path(path).expanduser()
    if not p.is_file():
        return f"Không tìm thấy file: {path}"
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        return f"Không đọc được file: {e}"
    if len(text) > _MAX_CHARS:
        return text[:_MAX_CHARS] + f"\n\n[...đã cắt bớt, file dài {len(text)} ký tự]"
    return text


@tool(
    "Tạo một thư mục mới (tạo cả thư mục cha nếu chưa có). An toàn nếu đã tồn tại.",
    path="Đường dẫn thư mục cần tạo.",
)
def create_dir(path: str) -> str:
    p = Path(path).expanduser()
    if p.exists():
        return f"Thư mục đã tồn tại: {p}" if p.is_dir() else f"Đã có file trùng tên, không tạo được thư mục: {p}"
    try:
        p.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        return f"Không tạo được thư mục: {e}"
    return f"Đã tạo thư mục: {p}"


@tool(
    "Di chuyển hoặc đổi tên một file. Nếu dest là thư mục, file được dồn vào trong đó. "
    "Mặc định KHÔNG ghi đè file đã tồn tại (đặt overwrite=true nếu muốn).",
    src="Đường dẫn file nguồn.",
    dest="Đường dẫn đích (file mới hoặc thư mục để dồn vào).",
    overwrite="True để ghi đè nếu đích đã tồn tại. Mặc định false.",
)
def move_file(src: str, dest: str, overwrite: bool = False) -> str:
    s = Path(src).expanduser()
    if not s.exists():
        return f"Không tìm thấy nguồn: {src}"
    d = Path(dest).expanduser()
    # Nếu đích là thư mục có sẵn -> giữ nguyên tên file, dồn vào trong.
    target = d / s.name if d.is_dir() else d
    if target.resolve() == s.resolve():
        return "Nguồn và đích trùng nhau, không cần di chuyển."
    if target.exists() and not overwrite:
        return f"Đích đã tồn tại: {target} (đặt overwrite=true nếu muốn ghi đè)."
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(s), str(target))
    except OSError as e:
        return f"Không di chuyển được: {e}"
    return f"Đã chuyển: {s.name} → {target}"
