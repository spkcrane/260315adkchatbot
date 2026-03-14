### Create Operations Agent ผ่าน Google ADK CLI
```bash
adk create operations_agent
```

### Create Operations Tools
```bash
touch tools/operation.py
```

### Install dateparser Dependency
```bash
pip install dateparser
```

### Update Code - Operation Tools
```python
from tools.vehicle import load_vehicle_data
from datetime import datetime, timedelta
import dateparser


def resolve_date(date_text: str):

    parsed = dateparser.parse(
        date_text,
        languages=["th", "en"],
        settings={
            "PREFER_DATES_FROM": "future"
        }
    )

    if not parsed:
        return {
            "success": False,
            "message": "Unable to parse date"
        }

    return {
        "success": True,
        "date": parsed.strftime("%Y-%m-%d")
    }

def check_vehicle_availability(model: str):
    """
    Check if a vehicle is available for test drive.
    """

    data = load_vehicle_data()
    specs = data.get("specs", {})

    if model in specs:
        return {
            "available": True,
            "model": model
        }

    return {
        "available": False,
        "model": model
    }


def check_schedule(date: str):
    """
    Return available test drive time slots.
    """

    return {
        "available_slots": [
            "10:30",
            "13:00",
            "15:30"
        ]
    }


def create_appointment(
    customer_name: str,
    customer_email: str,
    model: str,
    datetime: str
):
    """
    Create a test drive appointment.
    """

    appointment_id = "APT-" + datetime.replace(":", "").replace("-", "").replace(" ", "")

    return {
        "appointment_id": appointment_id,
        "status": "confirmed",
        "customer_name": customer_name,
        "customer_email": customer_email,
        "model": model,
        "datetime": datetime
    }
```

### Update Code - Operation Agent
```python
from google.adk import Agent
from tools.operation import (
    resolve_date,
    check_schedule,
    create_appointment
)
from tools.vehicle import (
    get_available_models
)
from tools.send_email import send_email

root_agent = Agent(
    name="OperationsAgent",
    model="gemini-2.5-flash",
    description="Handles operational tasks such as scheduling test drives and managing appointments",

    instruction="""
You are an Operations Agent for an automotive dealership.

Responsibilities:
- Schedule test drive appointments
- Check vehicle availability
- Check available schedule
- Create appointment
- Send confirmation email

Workflow:
1. Resolve relative dates (e.g. tomorrow, พรุ่งนี้) using resolve_date tool.
2. Check vehicle availability.
3. Check available schedule.
4. Create appointment (customer name and email required).
5. Send confirmation email after booking.

Language Rule:
- Always respond in the same language as the user.
- If the user writes in Thai, reply in Thai.
- If the user writes in English, reply in English.
- Do not mix languages in the same response.

Missing Information Rule:
- If customer name or email is missing, ask the user before creating the appointment.

Confirmation Message should include:
- Vehicle model
- Date and time
- Appointment ID
""",

    tools=[
        resolve_date,
        get_available_models,
        check_schedule,
        create_appointment,
        send_email
    ]
)
```