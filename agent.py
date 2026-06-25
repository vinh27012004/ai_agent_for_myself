"""Trợ lý cá nhân chạy trên terminal.

Cách dùng:
    python agent.py
Lệnh trong phiên: /help, /reset, /tools, /quit
"""
from __future__ import annotations

import io
import sys

# Đảm bảo in tiếng Việt không lỗi trên Windows console.
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import config
import llm
import tools

SYSTEM_PROMPT = """Bạn là trợ lý cá nhân của người dùng, trả lời bằng tiếng Việt, thân thiện và ngắn gọn.
Bạn có các công cụ: quản lý công việc/nhắc nhở, trí nhớ dài hạn, đọc & sắp xếp file, Gmail và Google Calendar.
Nguyên tắc:
- Khi người dùng nhờ ghi việc, đặt nhắc, hay hỏi về việc cần làm -> dùng tool tasks.
- Khi người dùng tiết lộ thông tin lâu dài về bản thân (sở thích, mục tiêu, người quen) -> chủ động remember().
- Đầu cuộc trò chuyện hoặc khi cần ngữ cảnh -> recall() để nhớ về người dùng.
- Khi cần nội dung file -> read_file. Đừng bịa nội dung file.
- Khi sắp xếp file: dùng list_dir để xem trước, create_dir để tạo thư mục, move_file để dồn file vào.
  Trước khi di chuyển NHIỀU file, hãy tóm tắt kế hoạch cho người dùng xem rồi mới làm. Không ghi đè file trừ khi được cho phép.
- Email & lịch: dùng search_emails/read_email để xem mail; list_events để xem lịch.
- Khi người dùng muốn xem tổng quan/tóm tắt/"báo cáo" ngày hôm nay -> create_daily_report.
- HÀNH ĐỘNG NHẠY CẢM (send_email, delete_event): LUÔN tóm tắt nội dung và HỎI XÁC NHẬN của người dùng trước khi thực hiện.
  Khi soạn mail mà người dùng chưa chắc, ưu tiên create_draft thay vì send_email.
- Thời gian cho Calendar dùng ISO 8601. Hôm nay là ngày được cung cấp trong ngữ cảnh; suy ra ngày cụ thể từ lời nói ('mai', 'thứ 6').
Luôn xác nhận ngắn gọn sau khi thực hiện hành động."""


def main() -> None:
    tools.load_all()
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    print("🤖 Trợ lý cá nhân — gõ /help để xem lệnh, /quit để thoát.")
    print(f"   (model: {config.MODEL} @ {config.BASE_URL})\n")

    while True:
        try:
            user = input("Bạn> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nTạm biệt!")
            break

        if not user:
            continue
        if user in ("/quit", "/exit"):
            print("Tạm biệt!")
            break
        if user == "/help":
            print("Lệnh: /daily_report (báo cáo hôm nay), /reset (xoá hội thoại), "
                  "/tools (liệt kê tool), /quit (thoát)")
            continue
        if user == "/reset":
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            print("Đã xoá lịch sử hội thoại.")
            continue
        if user == "/tools":
            for s in tools.get_schemas():
                fn = s["function"]
                print(f"  - {fn['name']}: {fn['description']}")
            continue
        if user == "/daily_report":
            from tools.report import build_report
            try:
                build_report(open_browser=True)
            except Exception as e:  # noqa: BLE001
                print(f"[Lỗi tạo báo cáo] {type(e).__name__}: {e}")
            continue

        messages.append({"role": "user", "content": user})
        try:
            reply = llm.chat(messages, on_tool=_show_tool)
        except Exception as e:  # noqa: BLE001
            print(f"[Lỗi gọi model] {type(e).__name__}: {e}")
            print("  → Kiểm tra AGENT_BASE_URL/API_KEY trong .env và kết nối tới VPS.")
            messages.pop()  # bỏ tin nhắn user lỗi để thử lại
            continue
        print(f"\n🤖 {reply}\n")


def _show_tool(name: str, args: str) -> None:
    print(f"  ⚙️  {name}({args})")


if __name__ == "__main__":
    main()
