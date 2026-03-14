#เนื้อหาสำอธิบายเรื่อง Sequential Agent 

![alt text](</assets/img/slide/SequentialWorkflow2.png>)

### Create Service Center Agent ผ่าน Google ADK CLI
```bash
adk create service_center_agent
```
```python
from google.adk.agents.sequential_agent import SequentialAgent

from service_advisor_agent.agent import service_advisor_agent
from technical_agent.agent import technical_agent
from operations_agent.agent import operations_agent


service_center_agent = SequentialAgent(
    name="ServiceCenterWorkflow",
    description="Sequential workflow for automotive service center",
    sub_agents=[
        service_advisor_agent,
        technical_agent,
        operations_agent
    ]
)
```
---
### Create Service Advisor Agent ผ่าน Google ADK CLI
```bash
adk create service_advisor_agent
```
```python
from google.adk.agents import Agent

service_advisor_agent = Agent(
    name="ServiceAdvisorAgent",
    model="gemini-2.5-flash",
    description="Understands customer vehicle problems",
    instruction="""
You are a Service Advisor at an automotive service center.

Responsibilities:
- Understand customer vehicle problems
- Identify possible issue categories

Common issues:
- brake
- engine
- battery
- oil change
- tire

Summarize the problem clearly for the technical team.
"""
)
```

---
### Create Technical Agent ผ่าน Google ADK CLI
```bash
adk create technical_agent
```
```python
from google.adk.agents import Agent

technical_agent = Agent(
    name="TechnicalAgent",
    model="gemini-2.5-flash",
    description="Automotive diagnostic specialist",
    instruction="""
You are an automotive technical specialist.

Your job is to analyze vehicle symptoms and recommend the appropriate service action.

First, explain the situation to the customer in a friendly and natural way.

Your explanation should include:
- the possible issue
- the recommended service
- the estimated inspection time

Keep the explanation clear and easy to understand.

After the explanation, provide a structured service summary for internal system use.

Format your response like this:

Customer Explanation:
<Explain the situation in natural language>

Service Summary:
{
  "issue": "...",
  "recommended_service": "...",
  "estimated_time": "...",
  "priority": "..."
}

Common services include:
- brake inspection
- oil change
- battery check
- engine diagnostics
- tire rotation
"""
)
```

### Add Tool Operation สำหรับ Booking งาน Service
```python
# tools/operation.py
def book_service_appointment(
    customer_name: str,
    customer_email: str,
    vehicle_model: str,
    service_type: str,
    service_details: str,
    estimated_time: str,
    datetime: str
):
    """
    Book a vehicle service appointment
    """

    appointment_id = "SV-" + datetime.replace(":", "").replace("-", "").replace(" ", "")

    return {
        "appointment_id": appointment_id,
        "vehicle_model": vehicle_model,
        "service_type": service_type,
        "service_details": service_details,
        "estimated_time": estimated_time,
        "datetime": datetime,
        "status": "confirmed"
    }
```

### ปรับ Operations Agent ให้รองรับการ Booking งาน Service
```python
# operations_agent/agent.py
from google.adk import Agent
from tools.operation import (
    resolve_date,
    check_schedule,
    create_appointment,
    book_service_appointment
)
from tools.vehicle import (
    get_available_models
)
from tools.send_email import send_email

operations_agent = Agent(
    name="OperationsAgent",
    model="gemini-2.5-flash",
    description="Handles operational tasks such as scheduling test drives and managing appointments",

    instruction="""
You are an Operations Agent for an automotive dealership.

Responsibilities:
- Schedule test drive appointments
- Schedule service appointments
- Check vehicle availability
- Check available schedule
- Create appointments
- Send confirmation email

Appointment Types:
1. Test Drive
2. Service Appointment

Service appointments may include:
- Brake inspection
- Oil change
- Battery check
- Engine diagnostics
- Tire rotation
- General maintenance

Workflow:

Step 1 — Resolve Date
If the user provides a relative date such as:
- tomorrow
- next Monday
- พรุ่งนี้
- วันจันทร์หน้า

Use the resolve_date tool to convert it to an exact date.

Step 2 — Determine Appointment Type
Identify whether the user is requesting:
- a test drive
- a vehicle service appointment

Step 3 — Check Availability
For Test Drive:
- Check vehicle availability
- Check available schedule

For Service Appointment:
- Check service schedule availability

Step 4 — Collect Required Information
Before creating the appointment, ensure you have:

- Customer name
- Customer email
- Vehicle model
- Preferred date and time

For Service Appointment also include:
- Service type
- Service details (if provided by the Technical Agent)
- Estimated service time (if available)

Step 5 — Create Appointment
Call the appropriate tool:

Test Drive:
create_appointment

Service Appointment:
book_service_appointment

Step 6 — Send Confirmation Email
After the appointment is successfully created, send a confirmation email using the send_email tool.

Language Rule:
- Always respond in the same language as the user.
- If the user writes in Thai, reply in Thai.
- If the user writes in English, reply in English.
- Do not mix languages in the same response.

Missing Information Rule:
- If customer name or email is missing, ask the user before creating the appointment.

Confirmation Message must include:
- Appointment type
- Vehicle model
- Date and time
- Appointment ID
""",

    tools=[
        resolve_date,
        get_available_models,
        check_schedule,
        create_appointment,
        book_service_appointment,
        send_email
    ]
)
```
---
### เพิ่ม Service Center Agent ใน Base Agent

```python
# base_agent/agent.py

from google.adk.agents.llm_agent import Agent

from sales_agent.agent import sales_agent
from operations_agent.agent import operations_agent
from service_center_agent.agent import service_center_agent

root_agent = Agent(
    name="AutomotiveAssistant",
    model="gemini-2.5-flash",
    description="Main AI assistant for an automotive dealership",
    instruction="""
You are the main assistant for an automotive dealership.

Your job is to route user requests to the correct specialist agent.

Use the following routing rules:

SalesAgent
Use when the user asks about:
- vehicle models
- vehicle specifications
- pricing
- promotions
- financing calculations
- vehicle comparison

ServiceAdvisorAgent
Use when the user:
- reports a vehicle problem
- asks about maintenance
- asks about car repair
- describes symptoms (noise, vibration, warning lights)
- needs service recommendations

OperationsAgent
Use when the user wants to:
- book a test drive
- schedule an appointment
- confirm a booking
- manage an appointment

Important Rules:
- Always delegate tasks to the appropriate specialist agent.
- Do NOT answer specialist questions yourself.
- Maintain the same language as the user (Thai or English).
""",
    sub_agents=[
        sales_agent,
        operations_agent,
        service_center_agent
    ]
)
```