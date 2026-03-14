#เนื้อหาสำอธิบายเรื่อง Multi Agent 

### Create Operations Agent ผ่าน Google ADK CLI
```bash
adk create base_agent
```

---

### Change Sales Agent to Sub Agent

เปิดไฟล์ sales_agent/agent.py แล้วเปลี่ยน root_agent เป็น sales_agent

```python
sales_agent = Agent(
```

---

### Change Operation Agent to Sub Agent

เปิดไฟล์ sales_agent/agent.py แล้วเปลี่ยน root_agent เป็น operations_agent

```python
operations_agent = Agent(
```
---

### Copy Code to Base Agent
```python
#base_agent/agent.py

from google.adk.agents.llm_agent import Agent

from sales_agent.agent import sales_agent
from operations_agent.agent import operations_agent


root_agent = Agent(
    name="AutomotiveAssistant",
    model="gemini-2.5-flash",
    description="Main AI assistant for an automotive dealership",
    instruction="""
You are the main assistant for an automotive dealership.

Your job is to route user requests to the correct specialist agent.

Use:
- SalesAgent → when the user asks about vehicles, specifications, pricing, or promotions.
- OperationsAgent → when the user wants to book, schedule, or manage test drive appointments.

Always delegate tasks to the appropriate agent instead of answering yourself.

Maintain the same language as the user (Thai or English).
""",
    sub_agents=[
        sales_agent,
        operations_agent
    ]
)
```
![alt text](</assets/img/slide/Screenshot 2569-03-11 at 22.07.16.png>)