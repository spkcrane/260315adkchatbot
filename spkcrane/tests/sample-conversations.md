# Sample Thai Test Conversations — SPKCrane Lead Bot

Copy-paste these messages into ADK Web UI to test each scenario.

---

## TC1: Happy Path (P1 → P2 → P3)

```
สวัสดีครับ
นิคมอุตสาหกรรมอมตะนคร ชลบุรี
20 เมษายน 2569
สยามก่อสร้าง
081-234-5678
ยกเครื่องจักร 3 ตัน สูง 15 เมตร
```
> **Expected:** Bot greets → P1(location→date) → P2(company→contact) → P3(details) → notify → confirmation.

## TC2: Happy Path (P3 skipped)

```
สวัสดีครับ
กรุงเทพ บางนา
พรุ่งนี้
ABC Engineering
089-111-2222
ไม่มีครับ
```
> **Expected:** Bot collects P1+P2, asks P3, customer declines, recorded as "-", notify fires.

## TC3: Vague Location + Re-ask (P1)

```
สวัสดีครับ
ไม่แน่ใจครับ
ก็แถวชลบุรี
```
> **Expected:** Bot re-asks once with example, then accepts "แถวชลบุรี" and continues to date.

## TC4: P2 Company + Contact

Start a normal flow, give location + date, then:
```
สยามก่อสร้าง
081-234-5678
```
> **Expected:** Bot asks company → contact in order after P1, then moves to P3.

## TC5: Price Before Any Lead Info

```
ราคาเช่าเครนเท่าไหร่ครับ
```
> **Expected:** Full 3-model price table + disclaimers, then asks location (P1).

## TC6: Price Mid-Collection

```
สวัสดีครับ
อมตะนคร ชลบุรี
ราคาเท่าไหร่ครับ
```
> **Expected:** Full price table, then asks date (next uncollected P1 field).

## TC7: Repeated Price Question

After seeing the full price table once, send:
```
ราคาเท่าไหร่ครับ
```
> **Expected:** Short reply, NOT the full table again. Includes "ยังไม่รวมค่าขนส่ง".

## TC8: Specific Model Price

```
เครน 4 ตันราคาเท่าไหร่ครับ
```
> **Expected:** Only 4.0 ตัน price (15,000 บาท/วัน) + transport disclaimer. Not the full table.

## TC9: Crane Model Recommendation

```
สวัสดีครับ
รุ่นไหนเหมาะกับงานยกเครื่องจักร 2 ตันครับ
```
> **Expected:** Bot deflects — "ทีมงานจะแนะนำรุ่นที่เหมาะสมให้ค่ะ". Does NOT recommend a model.

## TC10: Vague service_date (P1)

When asked about วันที่, send:
```
เร็วๆ นี้ครับ
```
Then:
```
ยังไม่แน่ใจ
```
> **Expected:** Bot re-asks once with example, then records "ไม่ระบุ" and moves to P2 (company).

## TC11: Chat After Completion

After the bot sends the "ขอบคุณค่ะ ... 🙏" confirmation, send:
```
ขอบคุณครับ
```
Then:
```
เปลี่ยนวันได้ไหมครับ
```
> **Expected:** Short polite reply both times. No restart. No re-collection.
