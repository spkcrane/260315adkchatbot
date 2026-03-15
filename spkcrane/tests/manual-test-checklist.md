# Manual Test Checklist — SPKCrane Lead Bot

Run these tests in ADK Web UI (`adk web --port 8000` → select `crane_lead_pipeline`).
Start a **new session** for each test case.

---

## Core Flow (P1 → P2 → P3)

| # | Test Case | Input Trigger | Pass? |
|---|-----------|--------------|-------|
| 1 | **Happy path** — P1(location+date) + P2(company+contact) + P3(details), notify fires | Complete all fields normally | ☐ |
| 2 | **P1: Vague location + re-ask** — bot re-asks once with example | Answer "ไม่แน่ใจ" for location | ☐ |
| 3 | **P2: Company + contact collected** — asks company then contact after P1 | Give location + date, then company + contact | ☐ |
| 4 | **P3: Details provided** — customer gives extra info (weight, height, etc.) | Answer "ยกเครื่องจักร 3 ตัน" when asked | ☐ |
| 5 | **P3: Details skipped** — customer says "ไม่มี", recorded as "-" | Answer "ไม่มีครับ" | ☐ |

## Pricing

| # | Test Case | Input Trigger | Pass? |
|---|-----------|--------------|-------|
| 6 | **Price before any lead info** — full table shown, then asks location | "ราคาเท่าไหร่ครับ" as first message | ☐ |
| 7 | **Price mid-collection** — full table shown, resumes next field | Ask "ราคาเท่าไหร่" after giving location | ☐ |
| 8 | **Repeated price question** — short reply, not full table again | Ask about price a second time | ☐ |
| 9 | **Specific model price** — only that model's price + transport disclaimer | "เครน 4 ตันราคาเท่าไหร่" | ☐ |

## Guardrails

| # | Test Case | Input Trigger | Pass? |
|---|-----------|--------------|-------|
| 10 | **Crane model recommendation blocked** — bot deflects to team | "รุ่นไหนเหมาะกับงานผมครับ" | ☐ |
| 11 | **Image message rejected** — polite text-only reply (LINE webhook only) | Send an image | ☐ |
| 12 | **Off-topic question blocked** — bot stays on track | "วันนี้อากาศเป็นยังไง" | ☐ |

## Edge Cases

| # | Test Case | Input Trigger | Pass? |
|---|-----------|--------------|-------|
| 13 | **Vague service_date** — bot re-asks with example | "เร็วๆ นี้" or "ยังไม่แน่ใจ" | ☐ |
| 14 | **Chat after completion** — short polite reply, no restart | Send "ขอบคุณครับ" after confirmation | ☐ |
| 15 | **Multiple messages after completion** — still no restart | Send 2-3 more messages | ☐ |

---

**Total: 15 test cases**
