# Expected Outcomes & Pass Criteria — SPKCrane Lead Bot

Each test case maps to the checklist in `manual-test-checklist.md` and sample inputs in `sample-conversations.md`.

---

## TC1: Happy Path (P1 → P2 → P3)

| Criterion | Pass |
|-----------|------|
| Bot greets naturally in Thai, then asks location (P1) | ☐ |
| Asks exactly 1 question per turn | ☐ |
| Follows priority order: P1(location→date) → P2(company→contact) → P3(details) | ☐ |
| Calls `notify_team_line` tool (visible in ADK Web event log) | ☐ |
| Emoji summary contains location, date, company, contact, and details | ☐ |
| Customer sees short confirmation: "ขอบคุณค่ะ ... ทีมจะติดต่อกลับ ... 🙏" | ☐ |

## TC2: P1 Vague Location + Re-ask

| Criterion | Pass |
|-----------|------|
| Bot re-asks location once with example | ☐ |
| After second vague answer, records "ไม่ระบุ" and moves to date | ☐ |
| Does NOT re-ask a third time | ☐ |

## TC3: P2 Company + Contact

| Criterion | Pass |
|-----------|------|
| Bot asks company after P1 is complete | ☐ |
| Bot asks contact number after company | ☐ |
| Then moves to P3 | ☐ |

## TC4: P3 Details Provided

| Criterion | Pass |
|-----------|------|
| Bot asks P3 after P1+P2 complete | ☐ |
| Customer's details (weight, height, etc.) recorded in summary | ☐ |

## TC5: P3 Details Skipped

| Criterion | Pass |
|-----------|------|
| Bot asks "มีข้อมูลเพิ่มเติมไหมคะ" after P1+P2 | ☐ |
| Customer says "ไม่มี", recorded as "-" | ☐ |
| Notify still fires with "-" for details | ☐ |

## TC6: Price Before Any Lead Info

| Criterion | Pass |
|-----------|------|
| Full 3-model price table shown | ☐ |
| Includes "ราคาอ้างอิงเบื้องต้น" — NOT "ใบเสนอราคา" | ☐ |
| Includes "ยังไม่รวมค่าขนส่ง" | ☐ |
| Immediately asks location (P1) after pricing | ☐ |

## TC7: Price Mid-Collection

| Criterion | Pass |
|-----------|------|
| Full price table shown | ☐ |
| Resumes with the correct next uncollected field (not from beginning) | ☐ |
| Previously collected fields are NOT re-asked | ☐ |

## TC8: Repeated Price Question

| Criterion | Pass |
|-----------|------|
| Does NOT show full 3-model table again | ☐ |
| Gives a shorter response | ☐ |
| Still mentions "ยังไม่รวมค่าขนส่ง" | ☐ |
| Continues lead collection after answering | ☐ |

## TC9: Specific Model Price

| Criterion | Pass |
|-----------|------|
| Shows ONLY the requested model's price | ☐ |
| Does NOT list all 3 models | ☐ |
| Mentions "ยังไม่รวมค่าขนส่ง" | ☐ |
| Continues lead collection after answering | ☐ |

## TC10: Crane Model Recommendation Blocked

| Criterion | Pass |
|-----------|------|
| Bot does NOT recommend a specific crane model | ☐ |
| Deflects to team: "ทีมงานจะแนะนำรุ่นที่เหมาะสมให้ค่ะ" (or similar) | ☐ |
| Continues lead collection | ☐ |

## TC11: Image Message (LINE Webhook Only)

| Criterion | Pass |
|-----------|------|
| Bot replies with text-only polite rejection | ☐ |
| Does NOT crash or produce an error | ☐ |

> **Note:** Image rejection is handled in `line_webhook.py`, not in ADK Web UI. Test this via LINE OA or skip in ADK Web.

## TC12: Vague service_date

| Criterion | Pass |
|-----------|------|
| Bot re-asks once with example | ☐ |
| After second vague answer, records "ไม่ระบุ" and moves to P2 (company) | ☐ |

## TC13: Chat After Completion

| Criterion | Pass |
|-----------|------|
| Bot responds with short polite message (not a wall of text) | ☐ |
| Does NOT restart lead collection from the beginning | ☐ |
| Does NOT re-ask any fields | ☐ |
| Mentions team has received the info | ☐ |
| Handles 2-3 follow-up messages consistently | ☐ |

---

## Global Pass Criteria (Apply to ALL Tests)

| Criterion | Pass |
|-----------|------|
| Bot always uses Thai (unless customer writes in English) | ☐ |
| Bot never estimates a final price or issues a quotation | ☐ |
| Bot never recommends a crane model | ☐ |
| Bot never analyzes images or photos | ☐ |
| Bot uses ค่ะ/คะ consistently (NOT ครับ) | ☐ |
| Bot asks exactly 1 question per turn | ☐ |
| Each message is concise (~50 chars when possible) | ☐ |
| Fields collected in priority order: P1 → P2 → P3 | ☐ |
