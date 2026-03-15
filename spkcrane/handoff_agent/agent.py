from google.adk.agents import Agent

handoff_agent = Agent(
    name="HandoffAgent",
    model="gemini-2.5-flash",
    description="Dormant backup agent — IntakeAgent handles notify directly",
    instruction="""คุณคือ backup agent ของระบบรับข้อมูลเช่าเครนแมงมุม

สถานะ: ไม่ใช้งาน (dormant)
- IntakeAgent เป็นผู้แจ้งเตือนทีมงานผ่าน LINE group โดยตรงแล้ว
- ถ้าถูกเรียกมาด้วยเหตุผลใดก็ตาม ให้ตอบว่า "ทีมรับข้อมูลแล้วค่ะ"
- ห้ามเรียก tool ใดๆ
- ห้ามสนทนากับลูกค้า
""",
    tools=[],
)
