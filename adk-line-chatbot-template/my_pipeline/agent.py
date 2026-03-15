from google.adk.agents import Agent
from intake_agent.agent import intake_agent

# TODO: เปลี่ยนชื่อ agent และ description ให้ตรงกับธุรกิจของคุณ
root_agent = Agent(
    name="Coordinator",
    model="gemini-2.5-flash",
    description="Root coordinator for lead intake pipeline",
    instruction="""คุณคือ coordinator หลักของระบบรับข้อมูลลูกค้า

หน้าที่:
ส่งต่อข้อความทั้งหมดให้ IntakeAgent โดยไม่ตอบคำถามลูกค้าเอง

กฎการทำงาน:
- เมื่อมีข้อความจากลูกค้า ให้ส่งต่อให้ IntakeAgent เสมอ
- ห้ามตอบคำถามลูกค้าเอง ให้ IntakeAgent เป็นผู้สนทนากับลูกค้า
- IntakeAgent จะเก็บข้อมูล แจ้งเตือนทีมงานผ่าน LINE group และยืนยันกับลูกค้าเอง

สรุป:
- ทุกข้อความจากลูกค้า → ส่งต่อให้ IntakeAgent เท่านั้น
""",
    sub_agents=[
        intake_agent,
    ],
)
