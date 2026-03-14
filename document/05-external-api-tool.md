# 👷 Start Create External API Tool 🛠️

### เข้า folder tools
```
cd tools
```

### สร้างไฟล์ send_email.py
```
touch send_email.py
```

### ✉️ Create Tool - Send Grid
```python
#send_email.py

import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


def send_email(
    to_email: str,
    subject: str,
    content: str
) -> str:
    """
    Send email using SendGrid.

    Args:
        to_email: recipient email address
        subject: email subject
        content: email body content

    Returns:
        success message
    """

    api_key = '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'

    if not api_key:
        return "Error: SENDGRID_API_KEY not set"

    message = Mail(
        from_email="pamornt.ai@gmail.com",
        to_emails=to_email,
        subject=subject,
        html_content=content
    )

    try:
        sg = SendGridAPIClient(api_key)
        response = sg.send(message)

        print(response.status_code)
        print(response.body)
        print(response.headers)

        return f"Email sent successfully. Status code: {response.status_code}"

    except Exception as e:
        return f"Failed to send email: {str(e)}"
```

### 🤖 Adding Tools to an Agent
```python
# agent.py
from google.adk.agents.llm_agent import Agent
from tools.vehicle import (
    get_available_models,
    get_vehicle_specs,
    calculate_monthly_payment,
    search_inventory
)
from tools.send_email import send_email

# สร้าง sales agent สำหรับ dealership
root_agent = Agent(
    model='gemini-2.5-flash',
    name='AutomotiveSalesAgent',
    description='Sales assistant with vehicle lookup and financing tools',
    instruction="""You are an expert automotive sales consultant for a Thai dealership.

You have access to comprehensive tools to help customers:
- Look up vehicle specifications
- Calculate financing options
- Search our inventory
- Search for available models

If a tool returns a LIST of vehicles: 
Format the result as a human-readable bullet list.

Always use the tools to provide accurate information.
Present information clearly in Thai currency (฿).
Help customers find the perfect vehicle based on their needs and budget.


You help send email notifications to customers.

When composing an email:
- Always format the email body to be clean and easy to read.
- Use simple HTML formatting suitable for email (paragraphs, headings, spacing).
- If the content contains a list of items, convert the list into a well-structured HTML table.
- Tables should include clear headers (<th>) and rows (<tr>) for each item.
- Keep the design simple and professional for email clients.

If the user asks to send an email,
use the send_email tool with the formatted HTML content as the body.
""",
    tools=[
        get_available_models,
        get_vehicle_specs,
        calculate_monthly_payment,
        search_inventory,
        send_email
    ]
)
=
```