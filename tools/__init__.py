"""Hệ thống tool: đăng ký, sinh schema cho LLM, và điều phối lời gọi.

Mỗi tool là một hàm Python được bọc bởi @tool. Khi import package này,
các module con (tasks, memory, files) tự đăng ký tool của chúng vào REGISTRY.
"""
from __future__ import annotations

import inspect
import json
from typing import Any, Callable, get_type_hints

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


def tool(description: str, /, **param_descriptions: str) -> Callable:
    """Decorator: biến một hàm thành tool mà LLM gọi được.

    - `description`: mô tả tool cho LLM (positional-only để tham số tool có thể
      tên 'description' mà không xung đột).
    - `param_descriptions`: mô tả từng tham số (key = tên tham số).
    Schema (kiểu, bắt buộc/không) được suy ra từ type hint + default.
    """

    def decorator(func: Callable) -> Callable:
        sig = inspect.signature(func)
        # Resolve type hint thật (vì 'from __future__ import annotations' biến
        # annotation thành chuỗi). Fallback nếu không resolve được.
        try:
            hints = get_type_hints(func)
        except Exception:  # noqa: BLE001
            hints = {}
        param_types: dict[str, type] = {}
        properties: dict[str, Any] = {}
        required: list[str] = []
        for pname, p in sig.parameters.items():
            ann = hints.get(pname, str)
            param_types[pname] = ann
            properties[pname] = {
                "type": _PY_TO_JSON.get(ann, "string"),
                "description": param_descriptions.get(pname, ""),
            }
            if p.default is inspect.Parameter.empty:
                required.append(pname)

        REGISTRY[func.__name__] = {
            "func": func,
            "types": param_types,
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


def _coerce(value: Any, target: type) -> Any:
    """Ép argument về đúng kiểu type hint (LLM hay trả số/bool dưới dạng chuỗi)."""
    if value is None or isinstance(value, target):
        return value
    if target is bool and isinstance(value, str):
        return value.strip().lower() in ("true", "1", "yes", "có", "co")
    if target in (int, float) and isinstance(value, str):
        try:
            return target(value.strip())
        except ValueError:
            return value
    return value


def dispatch(name: str, arguments: str | dict) -> str:
    """Gọi tool theo tên với arguments (chuỗi JSON hoặc dict). Trả chuỗi kết quả."""
    if name not in REGISTRY:
        return f"[lỗi] Không có tool tên '{name}'."
    args = json.loads(arguments) if isinstance(arguments, str) else (arguments or {})
    # Ép kiểu theo type hint của hàm để tránh "false"/"999" dạng chuỗi.
    types = REGISTRY[name].get("types", {})
    for pname, ann in types.items():
        if pname in args and ann in (bool, int, float):
            args[pname] = _coerce(args[pname], ann)
    try:
        result = REGISTRY[name]["func"](**args)
    except Exception as e:  # noqa: BLE001 - trả lỗi về cho LLM tự xử lý
        return f"[lỗi khi chạy {name}] {type(e).__name__}: {e}"
    return result if isinstance(result, str) else json.dumps(result, ensure_ascii=False)


def load_all() -> None:
    """Import các module tool để chúng tự đăng ký."""
    from . import tasks, memory, files, report  # noqa: F401
    # Gmail/Calendar cần Google libs + credentials.json; bỏ qua nếu chưa sẵn sàng.
    try:
        from . import gmail, calendar  # noqa: F401
    except ImportError:
        pass
