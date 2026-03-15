# ADK + LINE Chatbot Template

Template สำหรับสร้าง LINE chatbot ที่เก็บข้อมูลลูกค้า (lead intake) ด้วย Google ADK + LINE Messaging API
พร้อม clone ไปใช้กับธุรกิจอื่นได้ทันที — แค่เปลี่ยน prompt ใน `intake_agent/agent.py`

---

## โครงสร้าง Project

```
├── line_webhook.py          ← LINE webhook server (Flask)
├── my_pipeline/             ← Root agent (rename ตาม project)
│   └── agent.py             ← Coordinator — ส่งต่อให้ IntakeAgent
├── intake_agent/            ← Main conversational agent
│   └── agent.py             ← ★ ไฟล์หลักที่ต้อง customize ★
├── tools/
│   └── line_notify.py       ← ส่ง lead summary ไป LINE group
├── .env.example             ← Template ตัวแปร environment
├── .gitignore               ← ป้องกัน .env หลุดเข้า git
└── requirements.txt         ← Dependencies (pinned versions)
```

---

## Quick Start (8 ขั้นตอน)

### 1. Clone & Install

```bash
# Clone หรือ copy folder นี้
cd adk-line-chatbot-template
pip install -r requirements.txt
```

### 2. สร้าง LINE Official Account

1. ไปที่ [LINE Developers Console](https://developers.line.biz/)
2. สร้าง Provider → สร้าง **Messaging API Channel**
3. จดค่า **Channel Secret** และ **Channel Access Token** (long-lived)

### 3. สร้าง Gemini API Key

1. ไปที่ [Google AI Studio](https://aistudio.google.com/apikey)
2. สร้าง API Key
3. จดค่า API Key

### 4. ตั้งค่า Environment Variables

```bash
cp .env.example .env
```

แก้ไข `.env`:

```env
GOOGLE_GENAI_USE_VERTEXAI=FALSE
GOOGLE_API_KEY=your_gemini_api_key          ← ใส่ Gemini API key
CHANNEL_SECRET=your_line_channel_secret     ← ใส่ LINE Channel Secret
CHANNEL_ACCESS_TOKEN=your_line_access_token ← ใส่ LINE Access Token
LINE_GROUP_ID=your_team_line_group_id       ← ใส่ LINE Group ID ของทีม
```

> **หา LINE_GROUP_ID ได้อย่างไร?**
> เชิญ bot เข้า group → ส่งข้อความ → ดู webhook log จะเห็น group ID
> หรือใช้ LINE Bot Designer / webhook inspection tool

### 5. Customize Prompt (★ ขั้นตอนสำคัญที่สุด ★)

แก้ไขไฟล์ `intake_agent/agent.py` — ค้นหา `# TODO:` แล้วเปลี่ยนตามธุรกิจ:

| TODO | ต้องเปลี่ยนอะไร | ตัวอย่าง |
|------|-----------------|---------|
| **Persona** | ชื่อบทบาท + ชื่อธุรกิจ | "คุณคือแอดมินหญิงของร้านเช่าชุดแต่งงาน" |
| **Fields (P1-P4)** | ข้อมูลที่ต้องเก็บ | วันงาน, สถานที่, ไซส์, งบประมาณ |
| **Guardrails** | สิ่งที่ bot ห้ามทำ | ห้ามให้ส่วนลด, ห้ามรับจอง |
| **Pricing** | ราคาอ้างอิง (ถ้ามี) | ชุด A: 15,000, ชุด B: 25,000 |
| **Summary format** | รูปแบบสรุปส่ง LINE group | emoji + labels ตาม fields |

### 6. (Optional) Rename Pipeline Package

ถ้าต้องการเปลี่ยนชื่อ package:

1. Rename folder `my_pipeline/` → `your_project_name/`
2. แก้ import ใน `line_webhook.py`:
   ```python
   from your_project_name.agent import root_agent
   ```

### 7. ทดสอบด้วย ADK Web UI

```bash
adk web --port 8000
```

เปิด http://localhost:8000 → เลือก **my_pipeline** → ทดสอบสนทนา

> **หยุด adk web ก่อนขั้นตอนถัดไป** (ใช้ port เดียวกัน)

### 8. Run LINE Webhook + ngrok

```bash
# Terminal 1: run webhook server
python line_webhook.py

# Terminal 2: expose ด้วย ngrok
ngrok http 8000
```

ตั้งค่าใน LINE Developers Console:
1. Webhook URL → `https://<ngrok-url>/webhook`
2. เปิด "Use webhook" ✅
3. กด "Verify" ✅
4. ปิด auto-reply ใน LINE Official Account Manager

---

## Architecture

```
LINE OA ←→ line_webhook.py ←→ ADK Runner
                                    │
                              Root Agent (Coordinator)
                                    │
                              IntakeAgent
                              ├── สนทนากับลูกค้า
                              ├── เก็บข้อมูลทีละ field
                              └── เรียก notify_team_line tool
                                        │
                                  LINE Group (ทีมงาน)
```

### Key Patterns

- **Priority-based fields**: P1(บังคับ) → P2(บังคับ) → P3(optional) → P4(optional)
- **Duplicate guard**: `_notified_leads` hash set ป้องกันส่ง lead ซ้ำ
- **Reply token fallback**: ถ้า reply token หมดอายุ → ใช้ push message แทน
- **Loading animation**: แสดง typing dots ระหว่าง agent คิด
- **Synthetic text**: Image → `"[ลูกค้าส่งรูปภาพ]"`, Sticker → `"[ลูกค้าส่ง sticker]"`

---

## Known Limitations

| Limitation | Impact | Production Fix |
|------------|--------|----------------|
| In-memory sessions | Restart = สูญเสีย session | ใช้ Redis / Firestore |
| In-memory dedup | Restart = ส่ง lead ซ้ำได้ | ใช้ Redis / DB |
| `asyncio.run()` in Flask | ไม่รองรับ concurrent >2 users | ใช้ FastAPI / Quart |
| `print()` logging | ไม่มี log level | ใช้ Python `logging` module |
| Port 8000 conflict | `adk web` กับ `line_webhook.py` ใช้ port เดียวกัน | หยุดอันหนึ่งก่อน |

---

## Tips

- **ทดสอบด้วย `adk web` ก่อนเสมอ** — เร็วกว่าทดสอบผ่าน LINE
- **Prompt สำคัญที่สุด** — คุณภาพของ bot ขึ้นอยู่กับ prompt ใน `intake_agent/agent.py`
- **"ตอบลูกค้าก่อนเรียก tool"** — ป้องกัน bot เงียบหลังเก็บ field สุดท้าย
- **`runner.run()` return events** — ต้อง iterate ALL events ไม่ใช่แค่ `is_final_response()`
- **.env ต้องอยู่ใน .gitignore เสมอ** — ป้องกัน API keys หลุด
