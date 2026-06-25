"""Lưu trữ JSON đơn giản trên đĩa cho dữ liệu cá nhân."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from config import DATA_DIR


def _path(name: str) -> Path:
    return DATA_DIR / f"{name}.json"


def load(name: str, default: Any) -> Any:
    p = _path(name)
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return default


def save(name: str, data: Any) -> None:
    _path(name).write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
