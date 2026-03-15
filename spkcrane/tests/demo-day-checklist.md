# Demo Day Checklist — SPKCrane Lead Bot

---

## 1. Pre-Demo Setup

| # | Step | Done? |
|---|------|-------|
| 1 | Python 3.12+ installed | ☐ |
| 2 | `pip install google-adk flask uvicorn line-bot-sdk python-dotenv requests` | ☐ |
| 3 | `.env` file has real values (not `YOUR_*` placeholders) | ☐ |
| 4 | ADK Web starts without errors | ☐ |
| 5 | ngrok installed (if showing LINE integration) | ☐ |
| 6 | LINE OA webhook configured (if showing LINE integration) | ☐ |

## 2. Verify Environment Variables

Check `spkcrane/.env`:

```
GOOGLE_API_KEY=<real Gemini key>        ← required for all demos
CHANNEL_SECRET=<real LINE secret>       ← required for LINE demo only
CHANNEL_ACCESS_TOKEN=<real LINE token>  ← required for LINE demo only
LINE_GROUP_ID=<real group ID>           ← required for push notification only
```

**Quick check:** If `LINE_GROUP_ID` is still `YOUR_LINE_GROUP_ID`, the bot will skip push but still print the summary to console — safe for ADK Web demo.

## 3. Run ADK Web (for class demo)

```bash
cd spkcrane
adk web --port 8000
```

Open http://localhost:8000 → select **crane_lead_pipeline**.

## 4. Run LINE Webhook (for LINE demo)

```bash
cd spkcrane
python line_webhook.py
```

## 5. Avoid Port Conflict

**Both use port 8000.** Always stop one before starting the other:

```
Ctrl+C on adk web → then python line_webhook.py
  — or —
Ctrl+C on line_webhook.py → then adk web --port 8000
```

## 6. ngrok Setup (LINE demo only)

```bash
ngrok http 8000
```

Then:
1. Copy the `https://xxx.ngrok-free.app` URL
2. LINE Developers → Messaging API → Webhook URL → paste `https://xxx.ngrok-free.app/webhook`
3. Enable "Use webhook" → click "Verify" → should succeed
4. LINE Official Account Manager → disable auto-reply messages

## 7. Priority QA Scenarios (Test These First)

| Priority | Scenario | What to send |
|----------|----------|-------------|
| 🔴 1st | Happy path | Complete all 10 fields normally |
| 🔴 2nd | Price question | "ราคาเท่าไหร่ครับ" before any info |
| 🟡 3rd | Crane model blocked | "รุ่นไหนเหมาะกับงานผมครับ" |
| 🟡 4th | Vague answer + re-ask | Answer "ไม่แน่ใจ" for weight |
| 🟢 5th | Chat after completion | "ขอบคุณครับ" after 🙏 confirmation |

## 8. Architecture Walkthrough (for class)

Show these files in order:

| Step | File | What to explain |
|------|------|-----------------|
| 1 | `crane_lead_pipeline/agent.py` | Root coordinator — routes to sub-agents |
| 2 | `intake_agent/agent.py` | Conversational agent — Thai prompt, 9+1 fields, guardrails, pricing policy, notify tool |
| 3 | `handoff_agent/agent.py` | Backup agent — reads conversation history, formats + notifies |
| 4 | `tools/line_notify.py` | Push API tool — sends emoji summary to LINE group |
| 5 | `line_webhook.py` | Flask webhook — LINE SDK v3, ADK Runner, session management |

**Key points to highlight:**
- Multi-agent with `sub_agents` (not SequentialAgent)
- IntakeAgent has the tool directly → notification fires immediately
- Guardrails: price reference only, no model recommendation, no image analysis
- Post-completion behavior: no restart

## 9. Limitations to Mention Honestly

- **In-memory sessions** — restart = fresh conversation
- **Single-threaded Flask** — works for 1-2 users, not production
- **No persistent lead storage** — leads exist only in LINE group + console
- **Placeholder credentials** — must set real LINE keys before LINE demo
- **LLM non-determinism** — exact wording may vary between runs

## 10. Demo Script (5-minute flow)

### Part A: Architecture (1 min)
> "This is a multi-agent chatbot built with Google ADK for a spider crane rental company in Thailand."

Show the architecture diagram in README. Explain Root → Intake → Handoff.

### Part B: ADK Web Live Demo (2 min)
1. Open ADK Web UI
2. Send "สวัสดีครับ" — bot greets and asks first question
3. Answer 3-4 fields to show one-at-a-time flow
4. Send "ราคาเท่าไหร่" — show reference pricing mid-flow
5. Continue and complete all fields
6. Show the 🙏 confirmation message
7. Show console output: `[SKIP] notify_team_line` with the emoji summary

### Part C: Guardrails (1 min)
1. Ask "รุ่นไหนเหมาะครับ" → show deflection
2. Give a vague answer → show re-ask behavior
3. Send message after completion → show no-restart behavior

### Part D: LINE Integration (1 min, optional)
> "In production, this connects to LINE OA via webhook."

Show `line_webhook.py` briefly. If LINE is configured:
1. Send a message from LINE → show reply
2. Show team group receiving the emoji summary

### Wrap-up
> "Known limitations: in-memory sessions, single-threaded, no persistent storage. These are acceptable for MVP and can be addressed in production."
