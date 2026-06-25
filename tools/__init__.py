"""Hệ thống tool: đăng ký, sinh schema cho LLM, và điều phối lời gọi.

Mỗi tool là một hàm Python được bọc bởi @tool. Khi import package này,
các module con (tasks, memory, files) tự đăng ký tool của chúng vào REGISTRY.
"""
from __future__ import annotations

import inspect
import json
from typing import Any, Callable

# name -> {"func": callable, "schema": openai_function_schema}
REGISTRY: dict[str, dict[str, Any]] = {}

_PY_TO_JSON = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    list: "array",
    dict: "object",
}


def tool(description: str, **param_descriptions: str) -> Callable:
    """Decorator: biến một hàm thành tool mà LLM gọi được.

    - `description`: mô tả tool cho LLM.
    - `param_descriptions`: mô tả từng tham số (key = tên tham số).
    Schema (kiểu, bắt buộc/không) được suy ra từ type hint + default.
    """

    def decorator(func: Callable) -> Callable:
        sig = inspect.signature(func)
        properties: dict[str, Any] = {}
        required: list[str] = []
        for pname, p in sig.parameters.items():
            ann = p.annotation if p.annotation is not inspect.Parameter.empty else str
            json_type = _PY_TO_JSON.get(ann, "string")
            properties[pname] = {
                "type": json_type,
                "description": param_descriptions.get(pname, ""),
            }
            if p.default is inspect.Parameter.empty:
                required.append(pname)

        REGISTRY[func.__name__] = {
            "func": func,
            "schema": {
                "type": "function",
                "function": {
                    "name": func.__name__,
                    "description": description,
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "required": required,
                    },
                },
            },
        }
        return func

    return decorator


def get_schemas() -> list[dict[str, Any]]:
    """Danh sách schema để truyền vào tham số `tools` của API."""
    return [t["schema"] for t in REGISTRY.values()]


def dispatch(name: str, arguments: str | dict) -> str:
    """Gọi tool theo tên với arguments (chuỗi JSON hoặc dict). Trả chuỗi kết quả."""
    if name not in REGISTRY:
        return f"[lỗi] Không có tool tên '{name}'."
    args = json.loads(arguments) if isinstance(arguments, str) else (arguments or {})
    try:
        result = REGISTRY[name]["func"](**args)
    except Exception as e:  # noqa: BLE001 - trả lỗi về cho LLM tự xử lý
        return f"[lỗi khi chạy {name}] {type(e).__name__}: {e}"
    return result if isinstance(result, str) else json.dumps(result, ensure_ascii=False)


def load_all() -> None:
    """Import các module tool để chúng tự đăng ký."""
    from . import tasks, memory, files  # noqa: F401
