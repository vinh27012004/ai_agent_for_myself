# 🤖 AI Agent — Trợ lý cá nhân terminal

Trợ lý cá nhân chạy trong terminal, kết nối model qua endpoint **tương thích OpenAI**
([9router](https://github.com/decolua/9router)) và **tự gọi tool** (function-calling)
để hỗ trợ công việc hằng ngày: quản lý việc cần làm, ghi nhớ dài hạn, đọc & sắp xếp file.

---

## ✨ Tính năng

| Nhóm | Tool | Mô tả |
|------|------|-------|
| 🗂️ **Công việc** | `add_task`, `list_tasks`, `complete_task`, `delete_task` | Quản lý việc cần làm / nhắc nhở (lưu `data/tasks.json`) |
| 🧠 **Trí nhớ** | `remember`, `recall`, `forget` | Ghi nhớ thông tin lâu dài về bạn, sống qua mọi phiên (`data/memory.json`) |
| 📄 **File** | `list_dir`, `read_file`, `create_dir`, `move_file` | Đọc tài liệu, tạo thư mục, sắp xếp/dồn file (có guardrail, không ghi đè mặc định) |
| 📧 **Gmail** | `search_emails`, `read_email`, `create_draft`, `send_email` | Tìm/đọc email, soạn nháp, gửi mail (hỏi xác nhận trước khi gửi) |
| 📅 **Calendar** | `list_events`, `create_event`, `update_event`, `delete_event` | Xem/tạo/sửa/xoá sự kiện (hỏi xác nhận trước khi xoá) |

Agent hiểu tiếng Việt, **tự quyết định gọi tool nào** dựa trên câu bạn nói, và gọi
nhiều tool liên tiếp trong một lượt.

---

## 📦 Cài đặt

```powershell
# 1. Tạo & kích hoạt virtualenv (nếu chưa có)
python -m venv .venv
.venv\Scripts\Activate.ps1

# 2. Cài thư viện
pip install -r requirements.txt
```

## ⚙️ Cấu hình

Tạo file `.env` ở thư mục gốc (xem `.env.example`):

```ini
# Endpoint tương thích OpenAI (9router)
AGENT_BASE_URL=http://<host>:20128/v1
AGENT_API_KEY=sk-xxxxxxxxxxxx     # key sinh từ dashboard 9router
AGENT_MODEL=ai-agent-for-myself   # hoặc cc/claude-opus-4-8, cc/claude-sonnet-4-6...
AGENT_DATA_DIR=data
```

> ⚠️ `.env` chứa key thật, đã được `.gitignore` — **đừng commit/chia sẻ**.
>
> 💡 Khi chạy từ máy khác (không phải VPS), 9router yêu cầu **key hợp lệ sinh từ
> dashboard** cho truy cập remote; key local cũ sẽ bị `401`.

## 📧 Bật Gmail & Calendar (Google OAuth)

Cần làm 1 lần:

1. Vào [Google Cloud Console](https://console.cloud.google.com) → tạo Project → bật **Gmail API** + **Google Calendar API**
2. **OAuth consent screen**: chọn *External*, thêm email của bạn vào **Test users**
3. **Credentials → Create OAuth client ID → Desktop app** → tải `credentials.json` về thư mục dự án
4. Đăng nhập (mở trình duyệt, cấp quyền):
   ```powershell
   python auth_setup.py
   ```
   Token lưu vào `token.json`, lần sau không hỏi lại. Đổi quyền → xoá `token.json` chạy lại.

> Quyền agent xin: đọc/soạn/gửi Gmail + đọc/tạo/sửa/xoá sự kiện Calendar.
> Agent luôn hỏi xác nhận trước khi **gửi email** hoặc **xoá sự kiện**.

## 🚀 Chạy

```powershell
python agent.py
```

## 📊 Báo cáo tổng hợp hằng ngày

Bản tóm tắt trong ngày (lịch, việc cần làm, email chưa đọc, ghi nhớ) ra file HTML.
Ba cách chạy:

- **Trong agent:** gõ `/daily_report`
- **Nói tự nhiên:** *"tạo báo cáo hôm nay"* (agent gọi tool `create_daily_report`)
- **CLI / hẹn giờ:** `python -m tools.report [--open]`

Xuất ra `data/reports/<ngày>.html`. Giao diện sửa ở **`templates/daily_report.html`**
(Jinja2). Có thể hẹn giờ chạy mỗi sáng bằng **Task Scheduler** (Windows).

Lệnh trong phiên: `/help` · `/tools` · `/reset` (xoá hội thoại) · `/quit`

**Ví dụ trò chuyện:**
```
Bạn> Nhắc tôi mai gọi cho khách hàng lúc 9h
Bạn> Tôi thích họp vào buổi sáng, nhớ giúp tôi
Bạn> Trong thư mục D:\Downloads, gom ảnh vào thư mục Anh, tài liệu vào TaiLieu
```

---

## 🧱 Cấu trúc dự án

```
ai_agent_for_myself/
├── agent.py          # REPL terminal — điểm chạy chính
├── llm.py            # kết nối router + vòng lặp tool-calling
├── config.py         # đọc cấu hình từ .env
├── requirements.txt
├── .env              # endpoint/key/model (gitignore)
├── auth_setup.py     # chạy 1 lần để đăng nhập Google (tạo token.json)
├── templates/
│   └── daily_report.html  # template báo cáo (Jinja2, sửa giao diện ở đây)
├── credentials.json  # OAuth client của Google (gitignore — KHÔNG commit)
├── token.json        # token đã đăng nhập (gitignore — tự sinh)
├── tools/
│   ├── __init__.py   # @tool decorator + registry + dispatch + sinh schema
│   ├── store.py      # helper đọc/ghi JSON
│   ├── tasks.py      # quản lý công việc
│   ├── memory.py     # trí nhớ dài hạn
│   ├── files.py      # đọc & sắp xếp file
│   ├── google_auth.py # OAuth dùng chung cho Gmail/Calendar
│   ├── gmail.py      # tool Gmail
│   ├── calendar.py   # tool Calendar
│   └── report.py     # báo cáo hằng ngày (/daily_report, tool, CLI)
└── data/             # tasks.json, memory.json (gitignore)
```

**Luồng một câu hỏi:**
`agent.py` (nhận input) → `llm.py` (gửi tới model + tool) → model chọn tool →
`tools/*` thực thi, đọc/ghi `data/*.json` → model viết câu trả lời → `agent.py` in ra.

---

## 🔧 Thêm tool mới

Hệ thống tự đăng ký + tự sinh schema từ type hint. Chỉ cần viết 1 hàm với decorator
`@tool` trong một module dưới `tools/`, rồi thêm vào `load_all()` trong
`tools/__init__.py`:

```python
from . import tool

@tool(
    "Mô tả tool cho model.",
    city="Tên thành phố cần xem thời tiết.",
)
def get_weather(city: str) -> str:
    ...
    return "Hà Nội: 30°C, nắng"
```

Kiểu tham số và bắt buộc/không được suy ra tự động từ type hint + default.

---

## 🗺️ Lộ trình

- [x] Quản lý công việc / nhắc nhở
- [x] Trí nhớ dài hạn
- [x] Đọc & sắp xếp file
- [x] **Gmail** (đọc/soạn/gửi mail) — qua Google OAuth
- [x] **Calendar** (xem/tạo/sửa/xoá sự kiện) — qua Google OAuth
- [ ] Nhắc nhở chủ động (scheduler nền)
- [ ] Quản lý context (cắt/tóm tắt khi gần đầy)
- [ ] Đọc PDF/Word
```
