# SPKCrane Lead-Intake Chatbot

Google ADK multi-agent chatbot for a spider crane rental business in Thailand.
Collects lead information via Thai-first conversation, then notifies the team LINE group with a formatted summary.

---

## Architecture

```
Root Agent (CraneLeadCoordinator)
  └── IntakeAgent   → Thai-first conversation, collects 8 lead fields, notifies team
```

| Component | File | Role |
|-----------|------|------|
| **Root Agent** | `crane_lead_pipeline/agent.py` | Thin coordinator. Routes all customer messages to IntakeAgent. |
| **IntakeAgent** | `intake_agent/agent.py` | Multi-turn conversation. Collects fields one-by-one (P1→P2→P3→P4). Calls `notify_team_line` when complete. |
| **LINE Notify Tool** | `tools/line_notify.py` | Pushes formatted lead summary to team LINE group via push API. Includes duplicate guard. |
| **LINE Webhook** | `line_webhook.py` | Flask app. Receives LINE text/image/sticker messages, runs ADK agent, replies. Push fallback on token expiry. |

> **Note:** `handoff_agent/` exists as dormant backup code but is not registered in the active agent pipeline.

---

## Main Business Flow

```
1. Customer sends message via LINE OA (or ADK Web)
2. Root Agent delegates to IntakeAgent
3. IntakeAgent asks P1(location→date) → P2(company→contact) → P3(weight→radius→height) → P4(source) (~8 messages)
4. After fields collected → confirms to customer → formats emoji summary → calls notify_team_line
5. Customer sees: "ขอบคุณสำหรับข้อมูลค่ะ เดี๋ยวแอดมินเช็คข้อมูลให้นะคะ 🙏"
6. Team LINE group receives formatted lead summary
```

---

## Lead Fields (Priority-Based)

### P1 — ถามก่อน (บังคับ)

| # | Field | Thai Prompt | Purpose |
|---|-------|-------------|----------|
| 1 | `project_location` | หน้างานอยู่ที่ไหนคะ | ประเมินค่าขนส่ง |
| 2 | `service_date` | ต้องการใช้วันที่เท่าไหร่คะ | เช็คคิวเครน |

### P2 — ถามต่อ (บังคับ)

| # | Field | Thai Prompt | Purpose |
|---|-------|-------------|----------|
| 3 | `company_name` | ชื่อบริษัทคะ | ระบุหน่วยงาน |
| 4 | `contact_number` | เบอร์โทรติดต่อกลับค่ะ | ติดต่อกลับ |

### P3 — ถามเพิ่ม (optional ทุกข้อ ลูกค้าตอบ "ไม่ทราบ" ได้)

| # | Field | Thai Prompt | Purpose |
|---|-------|-------------|----------|
| 5 | `estimated_weight_ton` | น้ำหนักชิ้นงานประมาณกี่ตันคะ (ถ้าไม่ทราบข้ามได้ค่ะ) | เลือกรุ่นเครน |
| 6 | `working_radius_m` | ระยะยก ห่างจากตัวเครนกี่เมตรคะ | เลือกรุ่นเครน |
| 7 | `lift_height_m` | ต้องยกสูงกี่เมตรคะ | เลือกรุ่นเครน |

### P4 — ถามท้ายสุด (optional)

| # | Field | Thai Prompt | Purpose |
|---|-------|-------------|----------|
| 8 | `source_channel` | รู้จักเราจากช่องทางไหนคะ | Marketing tracking |

- If customer says "ไม่ทราบ" on P3/P4 → recorded as "-"
- P3 fields asked separately, one at a time

---

## Guardrails

| Rule | Behavior |
|------|----------|
| **No final quotation** | Bot provides reference daily pricing only, never a binding quote |
| **Reference daily pricing** | 2.9t: 12,000 ฿/day · 4.0t: 15,000 ฿/day · 6t: 25,000 ฿/day (transport not included, monthly is case-by-case) |
| **No crane model recommendation** | Deflects: "ทีมงานจะแนะนำรุ่นที่เหมาะสมให้ค่ะ" |
| **No image analysis** | Acknowledges image, re-asks current question |
| **Sticker handling** | Acknowledges sticker, re-asks current question. Never interprets as data. |
| **Re-ask once** | If answer is vague, re-asks with example. P1/P2: records whatever given. P3/P4: records "-". |
| **Post-completion** | Short polite reply. No restart. No re-collection. |
| **Duplicate guard** | `notify_team_line` uses in-memory hash set to prevent sending same lead twice |

---

## How to Run

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```env
GOOGLE_GENAI_USE_VERTEXAI=FALSE
GOOGLE_API_KEY=your_gemini_api_key
CHANNEL_SECRET=your_line_channel_secret
CHANNEL_ACCESS_TOKEN=your_line_access_token
LINE_GROUP_ID=your_team_line_group_id
```

### 3. Test with ADK Web UI

```bash
cd spkcrane
adk web --port 8000
```

Open http://localhost:8000 → select **crane_lead_pipeline**.

### 4. Run LINE Webhook Locally

> **Note:** Stop `adk web` first — both use port 8000.

```bash
cd spkcrane
python line_webhook.py
```

### 5. Expose with ngrok (local dev only)

```bash
ngrok http 8000
```

Then in LINE Developers console:
1. Set webhook URL to `https://<ngrok-url>/webhook`
2. Enable "Use webhook"
3. Click "Verify"
4. Disable auto-reply in LINE Official Account Manager

### 6. Deploy to Google Cloud Run (Production)

#### Prerequisites

- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) installed
- A GCP project with billing enabled
- Docker (if building locally) or Cloud Build (recommended)

#### Option A: Deploy from source (recommended, no Docker needed locally)

```bash
cd spkcrane

# First time: set project & enable APIs
gcloud config set project YOUR_GCP_PROJECT_ID
gcloud services enable run.googleapis.com cloudbuild.googleapis.com

# Deploy
gcloud run deploy spkcrane-bot \
  --source . \
  --region asia-southeast1 \
  --allow-unauthenticated \
  --set-env-vars "GOOGLE_GENAI_USE_VERTEXAI=FALSE" \
  --set-env-vars "GOOGLE_API_KEY=your_gemini_api_key" \
  --set-env-vars "CHANNEL_SECRET=your_line_channel_secret" \
  --set-env-vars "CHANNEL_ACCESS_TOKEN=your_line_access_token" \
  --set-env-vars "LINE_GROUP_ID=your_team_line_group_id" \
  --min-instances 0 \
  --max-instances 3 \
  --memory 512Mi \
  --timeout 120
```

#### Option B: Build & push Docker image manually

```bash
cd spkcrane

# Build
docker build -t asia-southeast1-docker.pkg.dev/YOUR_PROJECT/cloud-run-source-deploy/spkcrane-bot .

# Push
docker push asia-southeast1-docker.pkg.dev/YOUR_PROJECT/cloud-run-source-deploy/spkcrane-bot

# Deploy
gcloud run deploy spkcrane-bot \
  --image asia-southeast1-docker.pkg.dev/YOUR_PROJECT/cloud-run-source-deploy/spkcrane-bot \
  --region asia-southeast1 \
  --allow-unauthenticated \
  --set-env-vars "GOOGLE_GENAI_USE_VERTEXAI=FALSE,GOOGLE_API_KEY=xxx,CHANNEL_SECRET=xxx,CHANNEL_ACCESS_TOKEN=xxx,LINE_GROUP_ID=xxx" \
  --min-instances 0 \
  --max-instances 3 \
  --memory 512Mi \
  --timeout 120
```

#### After deployment

You will get a permanent URL like `https://spkcrane-bot-xxxxx-as.a.run.app`.

In LINE Developers console:
1. Set webhook URL to `https://spkcrane-bot-xxxxx-as.a.run.app/webhook`
2. Enable "Use webhook" ✅
3. Click "Verify" ✅
4. Disable auto-reply in LINE Official Account Manager

> **Tip:** Use `--min-instances 1` to avoid cold start delays (~$5-15/month).  
> **Tip:** Use Secret Manager for production secrets instead of `--set-env-vars`.

---

## Required Environment Variables

| Variable | Description |
|----------|-------------|
| `GOOGLE_API_KEY` | Gemini API key |
| `CHANNEL_SECRET` | LINE Messaging API channel secret |
| `CHANNEL_ACCESS_TOKEN` | LINE long-lived channel access token |
| `LINE_GROUP_ID` | LINE group ID for team notifications |

---

## Manual QA

Test files are in `tests/`:

| File | Contents |
|------|----------|
| `manual-test-checklist.md` | 15 checkbox test cases for ADK Web |
| `sample-conversations.md` | Copy-paste Thai test inputs for each scenario |
| `expected-outcomes.md` | Detailed pass/fail criteria per test case |

---

## Example Customer Flow

```
User: สวัสดีครับ
Bot:  สวัสดีค่ะ ยินดีให้บริการค่ะ หน้างานอยู่ที่ไหนคะ              ← P1
User: นิคมอมตะนคร ชลบุรี
Bot:  ต้องการใช้วันที่เท่าไหร่คะ                                     ← P1
User: 20 เมษายน
Bot:  ชื่อบริษัทคะ                                                   ← P2
User: สยามก่อสร้าง
Bot:  เบอร์โทรติดต่อกลับค่ะ                                          ← P2
User: 081-234-5678
Bot:  น้ำหนักชิ้นงานประมาณกี่ตันคะ (ถ้าไม่ทราบข้ามได้ค่ะ)           ← P3
User: 3 ตัน
Bot:  ระยะยก ห่างจากตัวเครนกี่เมตรคะ                                 ← P3
User: ไม่ทราบ
Bot:  ได้เลยค่ะ ต้องยกสูงกี่เมตรคะ                                   ← P3
User: 15 เมตร
Bot:  รู้จักเราจากช่องทางไหนคะ                                       ← P4
User: เห็นใน Facebook
Bot:  ขอบคุณสำหรับข้อมูลค่ะ เดี๋ยวแอดมินเช็คข้อมูลให้นะคะ 🙏
```

## Example Internal LINE Summary

```
🏗️ Lead ใหม่ — เช่าเครนแมงมุม
━━━━━━━━━━━━━━━━━━
📍 สถานที่: นิคมอมตะนคร ชลบุรี
📅 วันที่: 20 เมษายน
🏢 บริษัท: สยามก่อสร้าง
📞 เบอร์: 081-234-5678
⚖️ น้ำหนัก: 3 ตัน
📏 ระยะยก: -
📐 ความสูงยก: 15 เมตร
📣 รู้จักจาก: Facebook
━━━━━━━━━━━━━━━━━━
```

---

## Known Limitations

| Limitation | Impact | Cloud Run Note |
|------------|--------|----------------|
| **Placeholder credentials** in `.env` | Must replace all `YOUR_*` values before real LINE testing | Use `--set-env-vars` or Secret Manager |
| **In-memory sessions** | Conversation state lost on restart/scale | Cloud Run may recycle instances; sessions reset periodically |
| **`asyncio.run()` in Flask** | Works for low-medium traffic | gunicorn threads=4 handles moderate concurrency |
| **Port 8000 conflict** | `adk web` and `line_webhook.py` share port 8000 | Cloud Run uses PORT env var (8080); no conflict |
| **No persistent storage** | Lead data exists only in LINE group message and console logs | Consider Firestore/Cloud SQL for persistence |
