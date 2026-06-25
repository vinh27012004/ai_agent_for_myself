"""Lớp giao tiếp với LLM (endpoint tương thích OpenAI) + vòng lặp tool-calling.

`chat()` chạy một lượt hội thoại: gọi model, nếu model yêu cầu dùng tool thì
thực thi tool, đưa kết quả lại cho model, lặp đến khi model trả lời cuối cùng.
"""
from __future__ import annotations

from openai import OpenAI

import config
import tools

client = OpenAI(api_key=config.API_KEY, base_url=config.BASE_URL)

# Số vòng tool tối đa trong một lượt, tránh lặp vô hạn.
_MAX_STEPS = 8


def chat(messages: list[dict], on_tool=None) -> str:
    """Xử lý 1 lượt. `messages` được cập nhật tại chỗ (thêm assistant/tool).

    on_tool(name, args) -> callback tuỳ chọn để hiển thị tool đang chạy.
    Trả về nội dung văn bản cuối cùng của assistant.
    """
    schemas = tools.get_schemas()
    for _ in range(_MAX_STEPS):
        resp = client.chat.completions.create(
            model=config.MODEL,
            messages=messages,
            tools=schemas,
            tool_choice="auto",
        )
        msg = resp.choices[0].message

        if not msg.tool_calls:
            messages.append({"role": "assistant", "content": msg.content or ""})
            return msg.content or ""

        # Ghi lại yêu cầu gọi tool của assistant.
        messages.append(
            {
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in msg.tool_calls
                ],
            }
        )
        # Thực thi từng tool và đưa kết quả trở lại.
        for tc in msg.tool_calls:
            if on_tool:
                on_tool(tc.function.name, tc.function.arguments)
            result = tools.dispatch(tc.function.name, tc.function.arguments)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                }
            )

    return "[Đã đạt giới hạn số bước tool mà chưa có câu trả lời cuối.]"
