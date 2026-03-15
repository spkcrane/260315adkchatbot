# Know-How: สร้าง LINE Chatbot ด้วย Google ADK

บทเรียนทั้งหมดจากการพัฒนา SPKCrane Lead-Intake Chatbot — สรุปไว้เพื่ออ้างอิงใน project หน้า

> **Project:** SPKCrane — LINE chatbot เก็บข้อมูลลูกค้าเช่าเครนแมงมุม (Spider Crane)  
> **Stack:** Google ADK + Gemini 2.5 Flash + LINE Messaging API + Flask  
> **ภาษาหลัก:** Thai-first conversation

---

## สารบัญ

1. [Architecture Decisions](#1-architecture-decisions)
2. [Google ADK Patterns](#2-google-adk-patterns)
3. [LINE Messaging API Patterns](#3-line-messaging-api-patterns)
4. [Prompt Engineering Lessons](#4-prompt-engineering-lessons-thai-chatbot)
5. [Bugs & Pitfalls ที่เจอ + วิธีแก้](#5-bugs--pitfalls-ที่เจอ--วิธีแก้)
6. [Production Checklist](#6-production-checklist)

---

## 1. Architecture Decisions

### ทำไมใช้ Root Agent → IntakeAgent (ไม่ใช้ single agent)

Google ADK มี convention ที่ต้องมี `root_agent` ใน package หลัก (`crane_lead_pipeline/agent.py`) — ADK Web UI และ `adk web` ต้องหา `root_agent` เป็น entry point

```
Root Agent (CraneLeadCoordinator)
  └── IntakeAgent   ← ทำงานจริงทั้งหมด
```

แม้ว่าตอนนี้มี sub_agent ตัวเดียว แต่โครงสร้างนี้:
- **รองรับ expansion** — เพิ่ม agent ใหม่ได้ง่าย (เช่น QuotationAgent, FollowUpAgent)
- **ตาม ADK convention** — `adk web` ค้นหา `root_agent` ใน package level

### ทำไม HandoffAgent ถูก disable

ตอนแรกออกแบบให้ IntakeAgent เก็บข้อมูล → ส่งต่อให้ HandoffAgent → HandoffAgent เรียก `notify_team_line`

**ปัญหาที่เจอ:**
- **Duplicate notifications** — ทั้ง IntakeAgent และ HandoffAgent เรียก tool ซ้ำ
- **Routing ผิด** — Root Agent บางครั้ง route ไป HandoffAgent ก่อนเก็บข้อมูลครบ
- **ความซับซ้อนที่ไม่จำเป็น** — สำหรับ lead intake ง่ายๆ ไม่จำเป็นต้องมี 2 agents

**แก้โดย:**
- ให้ IntakeAgent เรียก `notify_team_line` tool ตรงเลย
- ลบ HandoffAgent ออกจาก `sub_agents` list (แต่เก็บไฟล์ไว้เป็น backup)
- Root Agent มี sub_agent ตัวเดียว = ไม่มี routing decision ผิด

### File Structure แบบ ADK Standard

```
spkcrane/                          ← project root
├── crane_lead_pipeline/           ← "pipeline" package — ADK หา root_agent ที่นี่
│   ├── __init__.py                ← from . import agent
│   └── agent.py                   ← root_agent = Agent(...)
├── intake_agent/                  ← sub-agent package
│   ├── __init__.py
│   └── agent.py                   ← intake_agent = Agent(...)
├── tools/                         ← shared tools
│   └── line_notify.py             ← notify_team_line function
├── line_webhook.py                ← Flask webhook server (ไม่ใช่ส่วนของ ADK)
└── .env                           ← API keys (gitignored)
```

**สำคัญ:** ชื่อ package ที่ `adk web` ใช้คือ folder ที่มี `agent.py` ที่ export `root_agent`  
เมื่อรัน `adk web` → dropdown จะแสดง `crane_lead_pipeline`

---

## 2. Google ADK Patterns

### Setup Runner + Session

```python
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part

APP_NAME = "my_app"
session_service = InMemorySessionService()

runner = Runner(
    agent=root_agent,
    app_name=APP_NAME,
    session_service=session_service,
)
```

### Session Management

ADK ใช้ session เก็บ conversation history — ต้อง map LINE user_id → ADK session_id

```python
user_sessions = {}  # LINE user_id → ADK session_id

def get_agent_response(user_message, user_id):
    if user_id not in user_sessions:
        session = asyncio.run(
            session_service.create_session(app_name=APP_NAME, user_id=user_id)
        )
        user_sessions[user_id] = session.id

    session_id = user_sessions[user_id]
    content = Content(role="user", parts=[Part(text=user_message)])
    events = runner.run(user_id=user_id, session_id=session_id, new_message=content)
    # ... process events
```

**ข้อจำกัด:** `InMemorySessionService` หายเมื่อ restart server  
**Production fix:** ใช้ persistent session store (Redis, Firestore, etc.)

### ⚠️ Event Processing — Gotcha สำคัญที่สุด

`runner.run()` return **generator ของ events** — แต่ละ event อาจมี:
- **Text part** — ข้อความตอบกลับ
- **Function call part** — agent เรียก tool (เช่น `notify_team_line`)
- **ทั้งสองแบบ** — ในบาง event text + function_call อยู่ด้วยกัน

**❌ วิธีที่ผิด (crash ได้):**

```python
# อันตราย! ถ้า event มี function_call ไม่ใช่ text จะ crash
for event in events:
    if event.content and event.content.parts:
        return event.content.parts[0].text  # TypeError!
```

**✅ วิธีที่ถูกต้อง:**

```python
last_text = None
for event in events:
    if event.content and event.content.parts:
        for part in event.content.parts:
            if part.text:
                last_text = part.text

return last_text or "ขออภัยค่ะ ระบบขัดข้อง"
```

**ทำไมต้อง iterate ALL events:**
1. Agent ส่ง text ก่อน (ตอบลูกค้า)
2. Agent ส่ง function_call (เรียก tool)
3. Tool ทำงาน → return result
4. Agent อาจส่ง text อีกครั้ง (หลัง tool ทำงานเสร็จ)

ถ้าหยุดที่ event แรก → อาจได้แค่ function_call → bot เงียบ

### Agent Definition

```python
intake_agent = Agent(
    name="IntakeAgent",
    model="gemini-2.5-flash",
    description="...",          # ใช้ให้ Root Agent ตัดสินใจ routing
    output_key="collected_lead", # เก็บผลลัพธ์ใน session state
    instruction="...",          # prompt หลัก (ดูหัวข้อ 4)
    tools=[notify_team_line],   # tools ที่ agent เรียกได้
)
```

- **`description`** — Root Agent อ่านค่านี้เพื่อตัดสินใจว่าจะ route ไป agent ไหน
- **`output_key`** — เก็บผลลัพธ์ใน session state ด้วย key นี้ (ใช้ส่งต่อระหว่าง agents)
- **`instruction`** — prompt ที่กำหนดพฤติกรรมทั้งหมดของ agent

### Transfer Between Agents

ADK สร้าง `transfer_to_agent` tool ให้อัตโนมัติเมื่อ Root Agent มี sub_agents  
Root Agent เรียก `transfer_to_agent("IntakeAgent")` → ADK route ข้อความไป IntakeAgent

ไม่ต้องเขียน transfer logic เอง — แค่ใส่ instruction ให้ Root รู้ว่าต้องส่งต่อเมื่อไหร่

---

## 3. LINE Messaging API Patterns

### Webhook Setup (Flask + line-bot-sdk v3)

```python
from linebot.v3 import WebhookHandler
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi, ReplyMessageRequest, TextMessage
from linebot.v3.webhooks import MessageEvent, TextMessageContent, ImageMessageContent, StickerMessageContent

configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)
messaging_api = MessagingApi(ApiClient(configuration))

@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    handler.handle(body, signature)
    return "OK"

@handler.add(MessageEvent, message=TextMessageContent)
def handle_text(event):
    # process event...
```

**สำคัญ:** ใช้ `line-bot-sdk` v3 (ไม่ใช่ v2) — import path ต่างกัน:
- v3: `from linebot.v3.messaging import ...`
- v2: `from linebot import LineBotApi` (deprecated)

### Reply Token Expiry → Push Fallback

LINE reply token หมดอายุภายใน ~30 วินาที — ถ้า agent ใช้เวลาคิดนานหรือเรียก tool หลายตัว token อาจหมดอายุ

```python
def _handle_event(event, agent_text, label, fallback):
    line_user_id = event.source.user_id
    try:
        reply_text = get_agent_response(agent_text, line_user_id)
    except Exception:
        reply_text = fallback

    try:
        messaging_api.reply_message(ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[TextMessage(text=reply_text)],
        ))
    except Exception:
        # Reply token expired → fallback to push message
        push_message(line_user_id, reply_text)
```

**Push message** ไม่ต้องใช้ reply token แต่มี quota limit (free plan = 500 msg/month)

```python
def push_message(user_id, text):
    requests.post(
        "https://api.line.me/v2/bot/message/push",
        headers={"Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}", ...},
        json={"to": user_id, "messages": [{"type": "text", "text": text}]},
    )
```

### Loading Animation

แสดง "typing..." ระหว่าง agent กำลังคิด — ทำให้ user รู้ว่า bot ยังทำงานอยู่

```python
def show_loading_animation(chat_id, seconds=20):
    requests.post(
        "https://api.line.me/v2/bot/chat/loading/start",
        headers={"Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}", ...},
        json={"chatId": chat_id, "loadingSeconds": seconds},
    )
```

**ข้อจำกัด:** ใช้ได้เฉพาะ 1:1 chat (ไม่ใช้ใน group/room)  
**ค่า seconds:** 5-60 วินาที (จะหยุดเองเมื่อ bot ส่งข้อความ)

### Image/Sticker → Synthetic Text

LINE ส่ง image/sticker เป็น event type ต่างจาก text — ADK agent รับได้แค่ text  
**วิธีแก้:** แปลงเป็น "synthetic text" แล้วส่งเข้า agent

```python
@handler.add(MessageEvent, message=ImageMessageContent)
def handle_image(event):
    _handle_event(event, agent_text="[ลูกค้าส่งรูปภาพ]", ...)

@handler.add(MessageEvent, message=StickerMessageContent)
def handle_sticker(event):
    _handle_event(event, agent_text="[ลูกค้าส่ง sticker]", ...)
```

แล้วใน agent prompt กำหนดว่า:
- `"[ลูกค้าส่งรูปภาพ]"` → ตอบ "ขอบคุณสำหรับภาพค่ะ" + ถามคำถามเดิมซ้ำ
- `"[ลูกค้าส่ง sticker]"` → ตอบ "ขอบคุณค่ะ" + ถามคำถามเดิมซ้ำ
- **ห้ามตีความ** sticker/image เป็นคำตอบของ field

### DRY Pattern สำหรับหลาย Message Type

แทนที่จะเขียน handler ซ้ำ 3 ตัว ใช้ helper function:

```python
def _handle_event(event, agent_text: str, label: str, fallback: str):
    """Common handler: send agent_text to ADK, reply to LINE."""
    line_user_id = event.source.user_id
    show_loading_animation(line_user_id)
    reply_text = get_agent_response(agent_text, line_user_id)
    try:
        messaging_api.reply_message(...)
    except:
        push_message(line_user_id, reply_text)

# แต่ละ handler เหลือแค่ 5 บรรทัด
@handler.add(MessageEvent, message=TextMessageContent)
def handle_text(event):
    _handle_event(event, agent_text=event.message.text, label=event.message.text, fallback="...")

@handler.add(MessageEvent, message=ImageMessageContent)
def handle_image(event):
    _handle_event(event, agent_text="[ลูกค้าส่งรูปภาพ]", label="[image]", fallback="...")
```

---

## 4. Prompt Engineering Lessons (Thai Chatbot)

### Priority-Based Field Collection

แบ่ง fields เป็น 4 ระดับความสำคัญ:

| Priority | บังคับ? | พฤติกรรมเมื่อลูกค้าตอบ "ไม่ทราบ" |
|----------|---------|----------------------------------|
| **P1** | ✅ บังคับ | ถามซ้ำ 1 ครั้งพร้อมตัวอย่าง ห้ามข้าม |
| **P2** | ✅ บังคับ | ถามซ้ำ 1 ครั้งพร้อมตัวอย่าง ห้ามข้าม |
| **P3** | ❌ optional | บันทึก "-" แล้วข้ามไปข้อถัดไปทันที |
| **P4** | ❌ optional | บันทึก "-" แล้วข้ามไปข้อถัดไปทันที |

**ข้อดี:**
- ลูกค้าไม่รู้สึกถูกบังคับ — P3/P4 ข้ามได้สบายๆ
- ข้อมูลสำคัญ (P1/P2) ได้ครบเสมอ
- ถามตามลำดับ → สนทนาเป็นธรรมชาติ

### Prompt: "ตอบลูกค้าก่อนเรียก Tool"

**ปัญหา:** เมื่อ agent เก็บ field สุดท้ายครบ → เรียก `notify_team_line` → แต่ไม่ส่ง text กลับลูกค้า → bot เงียบ

**วิธีแก้ใน prompt:**

```
เมื่อเก็บข้อมูลครบทุกรายการ:
1. ตอบลูกค้าก่อนเลยว่า "ขอบคุณสำหรับข้อมูลค่ะ เดี๋ยวแอดมินเช็คข้อมูลให้นะคะ 🙏"
2. จากนั้นจัดรูปแบบข้อความสรุป...
3. เรียกใช้ tool notify_team_line

สำคัญมาก: ต้องตอบลูกค้าก่อนเรียก tool เสมอ ห้ามเรียก tool โดยไม่ตอบลูกค้า
```

**เคล็ดลับ:** เน้นย้ำ 2 จุดในพร้อมท์ — ทั้งตรงขั้นตอน (ข้อ 1 ก่อน ข้อ 3) และย่อหน้าสุดท้าย ("สำคัญมาก")

### Persona Consistency

```
สไตล์การตอบ:
- ตอบสั้น กระชับ แต่ละข้อความไม่เกิน 50 ตัวอักษรถ้าเป็นไปได้
- ใช้คำลงท้ายว่า "ค่ะ" หรือ "คะ" เสมอ ห้ามใช้ "ครับ"
- ไม่เกริ่นยาว ไม่อธิบายเกินจำเป็น ตรงประเด็น
- สุภาพแบบแอดมินมืออาชีพ
```

**ทำไมต้องชัดเจนขนาดนี้:**
- Gemini มักตอบยาว → ต้องบอก "ไม่เกิน 50 ตัวอักษร"
- Gemini สลับ ค่ะ/ครับ ได้ → ต้องบอก "ห้ามใช้ ครับ"
- ถ้าไม่ระบุ persona → bot จะตอบแบบ generic AI ไม่เหมือนแอดมินจริง

### Guardrails Pattern

กำหนด "สิ่งที่ห้ามทำ" ชัดเจน — ป้องกัน LLM hallucinate หรือตอบนอกขอบเขต

```
สิ่งที่ห้ามทำ:
- ห้ามให้ราคาสุดท้ายหรือใบเสนอราคา
- ห้ามแนะนำรุ่นเครนหรือยี่ห้อเครน
- ห้ามวิเคราะห์รูปภาพ
- ห้ามตอบคำถามนอกเหนือจากการรับข้อมูลเช่าเครน
- ห้ามเริ่มเก็บข้อมูลใหม่ตั้งแต่ต้น
```

**เคล็ดลับ:**
- ใช้ "ห้าม" แทน "ไม่ควร" — LLM เข้าใจ negative constraint ชัดกว่า
- ให้ทางออกด้วย — "ห้ามแนะนำรุ่น ถ้าลูกค้าถาม ให้ตอบว่า 'ทีมงานจะแนะนำรุ่นที่เหมาะสมให้ค่ะ'"

### Edge Case Handling

**Image/Sticker ระหว่าง intake:**
```
- ถ้าลูกค้าส่งรูป → ตอบ "ขอบคุณสำหรับภาพค่ะ" แล้วถามคำถามเดิมซ้ำ (ห้ามข้ามคำถาม)
- ถ้าลูกค้าส่ง sticker → ตอบ "ขอบคุณค่ะ" แล้วถามคำถามเดิมซ้ำ (ห้ามข้ามคำถาม)
- ห้ามตีความ sticker/รูปภาพเป็นข้อมูล lead
```

**"ไม่ทราบ" + Follow-up question:**
```
ถ้าลูกค้าตอบ "ไม่ทราบค่ะ เดี๋ยวถามหน้างานให้ก่อนได้ไหมคะ"
→ ตอบ "ได้เลยค่ะ" แล้วถามข้อถัดไปทันทีในข้อความเดียวกัน
```

**ราคากลาง intake flow:**
```
ถ้าลูกค้าถามเรื่องราคา → ให้ราคาอ้างอิงสั้นๆ → แล้วถามคำถามถัดไปต่อทันที
(ไม่หยุด flow)
```

### Prompt Contradiction — สิ่งที่ต้องระวัง

**ปัญหาที่เจอ:** Prompt มีกฎ 2 ข้อที่ขัดแย้งกัน:
- "ถ้าถามซ้ำแล้วยังไม่ได้คำตอบ → บันทึก '-' แล้วข้าม" (ใช้กับทุก field)
- "P1/P2 ห้ามข้าม" (ใช้เฉพาะ P1/P2)

LLM จะ pick กฎที่เห็นก่อน (หรือกฎที่ชัดกว่า) → พฤติกรรมไม่คงที่

**วิธีแก้:** ทำให้กฎไม่ซ้ำซ้อน — รวมเป็นกฎเดียวที่ครอบคลุมทุกกรณี:
```
ถ้าถามซ้ำแล้วยังไม่ได้คำตอบ: 
  P1/P2 → บันทึกสิ่งที่ลูกค้าตอบมาแล้วไปข้อถัดไป
  P3/P4 → บันทึก "-" แล้วข้ามทันที
```

---

## 5. Bugs & Pitfalls ที่เจอ + วิธีแก้

### Bug 1: Bot เงียบเมื่อตอบ field สุดท้าย

| | |
|---|---|
| **อาการ** | ลูกค้าส่ง field สุดท้าย → bot ไม่ตอบ → ต้องส่งอีกข้อความถึงจะเห็นคำตอบ |
| **Root cause** | Agent เรียก `notify_team_line` tool แต่ไม่สร้าง text response ก่อน → event loop จับได้แค่ function_call |
| **Fix (prompt)** | เพิ่ม "ตอบลูกค้าก่อนเรียก tool เสมอ" + เน้นลำดับ 1→2→3 |
| **Fix (code)** | Iterate ALL events เก็บ `last_text` แทนที่จะใช้แค่ event แรก |

### Bug 2: `parts[0].text` crash เป็น TypeError

| | |
|---|---|
| **อาการ** | `TypeError: 'NoneType' object is not subscriptable` |
| **Root cause** | `event.content.parts[0]` เป็น function_call part ไม่มี `.text` |
| **Fix** | Loop through all parts: `for part in event.content.parts: if part.text: ...` |

### Bug 3: Sticker/Image ข้าม required field

| | |
|---|---|
| **อาการ** | ลูกค้าส่ง sticker ตอนกำลังถาม "สถานที่" → bot ข้ามไปถาม "วันที่" |
| **Root cause** | Prompt บอก "ตอบขอบคุณแล้วถามข้อถัดไป" → agent เข้าใจว่าต้องข้ามไป field ใหม่ |
| **Fix** | เปลี่ยนเป็น "ถามคำถาม**เดิม**ที่กำลังถามอยู่ซ้ำ **ห้ามข้าม**คำถาม" |

### Bug 4: "ไม่ทราบ" ข้าม P1/P2

| | |
|---|---|
| **อาการ** | ลูกค้าตอบ "ไม่ทราบ" กับ required field → bot ข้ามไป field ถัดไป |
| **Root cause** | Prompt skip rule เขียนแบบ generic ใช้กับทุก field |
| **Fix** | แยกกฎ: P1/P2 re-ask + ตัวอย่าง, P3/P4 skip ทันที |

### Bug 5: Duplicate LINE notification

| | |
|---|---|
| **อาการ** | ทีมได้ lead เดียวกัน 2 ครั้งใน LINE group |
| **Root cause** | Agent เรียก `notify_team_line` tool ซ้ำ (retry หรือ HandoffAgent เรียกซ้ำ) |
| **Fix** | เพิ่ม `_notified_leads` hash set guard ใน `notify_team_line` function |

### Bug 6: API keys หลุดเข้า git

| | |
|---|---|
| **อาการ** | `.env` ที่มี real API keys ถูก commit |
| **Root cause** | ไม่มี `.gitignore` |
| **Fix** | สร้าง `.gitignore` ที่ block `.env` + สร้าง `.env.example` สำหรับ template |

### Bug 7: HandoffAgent ถูก route ผิด

| | |
|---|---|
| **อาการ** | บางครั้ง Root Agent ส่งข้อความไป HandoffAgent แทน IntakeAgent |
| **Root cause** | HandoffAgent ยังอยู่ใน `sub_agents` list → Root Agent มี 2 ตัวเลือก routing |
| **Fix** | ลบ HandoffAgent ออกจาก `sub_agents` → Root Agent มีทางเลือกเดียว |

---

## 6. Production Checklist

สิ่งที่ต้องเปลี่ยนก่อน deploy จริง:

### Must-Have

- [ ] **Persistent sessions** — เปลี่ยน `InMemorySessionService` → Redis / Firestore  
  (restart server = สูญเสีย conversation history ทั้งหมด)

- [ ] **Persistent dedup** — เปลี่ยน `_notified_leads` in-memory set → Redis / DB  
  (restart = dedup guard หาย → ส่ง lead ซ้ำได้)

- [ ] **Async framework** — เปลี่ยน Flask + `asyncio.run()` → FastAPI / Quart  
  (`asyncio.run()` สร้าง event loop ใหม่ทุกครั้ง — ไม่รองรับ concurrent >2-3 users)

- [ ] **Proper logging** — เปลี่ยน `print()` → Python `logging` module  
  (ต้องมี log level: DEBUG, INFO, WARNING, ERROR)

### Nice-to-Have

- [ ] **Catch-all message handler** — เพิ่ม handler สำหรับ video/audio/file/location  
  (ตอนนี้ bot เงียบเมื่อได้ message type ที่ไม่รองรับ)

- [ ] **Error monitoring** — เพิ่ม Sentry / Cloud Logging  
  (ตอนนี้ error แค่ print ไม่มี alert)

- [ ] **Rate limiting** — ป้องกัน bot ถูก spam  
  (LINE มี rate limit อยู่แล้ว แต่ agent call Gemini API ซึ่งมี quota)

- [ ] **Webhook signature verification** — ทำอยู่แล้ว ✅ (ผ่าน `WebhookHandler`)

- [ ] **Health check endpoint** — ทำอยู่แล้ว ✅ (GET `/` return status)

- [ ] **Lead storage** — เก็บ lead ลง database ด้วย (ตอนนี้มีแค่ใน LINE group message)

---

## Quick Reference

### Environment Variables

| Variable | ใช้ทำอะไร | หาจากไหน |
|----------|----------|----------|
| `GOOGLE_API_KEY` | Gemini API | [AI Studio](https://aistudio.google.com/apikey) |
| `CHANNEL_SECRET` | LINE webhook verification | LINE Developers Console → Channel |
| `CHANNEL_ACCESS_TOKEN` | LINE API calls | LINE Developers Console → Channel → Long-lived token |
| `LINE_GROUP_ID` | ส่ง lead ไปกลุ่มไหน | เชิญ bot เข้า group → ดู webhook log |

### Commands

```bash
# ทดสอบด้วย ADK Web UI
adk web --port 8000

# Run LINE webhook
python line_webhook.py

# Expose ด้วย ngrok
ngrok http 8000
```

### Key Files

| ไฟล์ | แก้เมื่อไหร่ |
|------|-------------|
| `intake_agent/agent.py` | เปลี่ยน prompt, fields, persona, guardrails |
| `line_webhook.py` | เปลี่ยน webhook behavior, message handling |
| `tools/line_notify.py` | เปลี่ยน notification format/destination |
| `crane_lead_pipeline/agent.py` | เพิ่ม/ลด sub_agents |
| `.env` | เปลี่ยน API keys |
