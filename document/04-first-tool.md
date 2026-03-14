# Adding Tools to Your Agent

## 🎯 Objective
เรียนรู้การเพิ่ม tools และ capabilities ให้ agent ใน Google ADK เพื่อเพิ่มฟังก์ชันการต่างๆ

---

## 🛠️ What are Agent Tools?

**Tools** คือ Python functions ที่ agent สามารถเรียกใช้เพื่อ:
- **ดึงข้อมูล** จาก external sources
- **ดำเนินการ** operations ต่างๆ
- **คำนวณ** หรือ process ข้อมูล
- **ติดต่อ** กับ APIs หรือ databases

### Tools vs Plain AI Knowledge

| Plain AI | With Tools |
|----------|-----------|
| General knowledge | Specific to business |
| Can't update in real-time | Real-time data access |
| Generic responses | Personalized responses |
| No external actions | Integration with systems |

---

## 🔧 Tool Structure in Google ADK

### Requirements for Tools

ใน Google ADK Python tools ต้อง:
1. เป็น Python function ทั่วไป
2. มี **type hints** สำหรับ parameters และ return
3. มี **docstring** อธิบาย purpose และ parameters
4. Return ค่าที่ JSON-serializable (dict, str, int, bool, list)

---
# 👷 Start Create Tool 🛠️

## 💿 COPY Data to Workshop
ตรวจสอบก่อนว่าตอนนี้อยู๋ที่ folder /workshop
```bash
cp -r ../data ./
```
---
# 🤖 Agent with Single 🔨 Tools

### สร้าง folder tools
```
mkdir tools
```
### เข้า folder tools
```
cd tools
```

### สร้างไฟล์ __init.py และ vehicle.py
```
touch __init__.py & touch vehicle.py
```

## Create Tool - Available Car Model

Copy Code ใส่ในไฟล์ tools/vehicle.py
```python
# vehicle.py
from typing import Dict, Optional, Any
import json
import re
import os

def load_vehicle_data() -> Dict[str, Any]:
    """Load vehicle data from ../data/vehicle_data.md"""
    path = os.path.join(os.path.dirname(__file__), '../data/vehicle_data.md')
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
    if match:
        return json.loads(match.group(1))
    return {}

def get_available_models() -> list[str]:
    """Get list of available vehicle models.
    
    Returns:
        List of unique vehicle models in inventory
    """
    data = load_vehicle_data()
    specs = data.get('specs', {})
    return list(specs.keys())
```

## 🤖 Adding Tools to an Agent
replace code ที่ไฟล์ sales_agent/agent.py
```python
# agent.py
from google.adk.agents.llm_agent import Agent
from tools.vehicle import (
    get_available_models
)

# สร้าง sales agent สำหรับ dealership
root_agent = Agent(
    model='gemini-2.5-flash',
    name='SalesAgent',
    description='Sales assistant with vehicle lookup and financing tools',
    instruction="""You are an expert automotive sales consultant for a Thai dealership.

You have access to comprehensive tools to help customers:
- Search for available models
""",
    tools=[
        get_available_models
    ]
)
```
---
## 🔧 Test - Run Command in Terminal
``` bash
cd ..
adk web
```

![alt text](</assets/img/slide/SalesAgentTools_1.png>)

## ทดสอบเปลี่ยน Format การ Response
```python
# เพิ่มเข้า Instructions ใน agent.py

If a tool returns a LIST of vehicles: 
Format the result as a human-readable bullet list.
```
---
# 🤖 Agent with Multiple 🛠️ Tools

## ⛏️ Create Tool - Car Specification
เพิ่ม function เข้าไปที่ไฟล์ tools/vehicle.py
```python
#tools/vehicle.py

def get_vehicle_specs(model_name: str) -> Dict[str, Any]:
    """Get specifications for a vehicle model.
    
    Args:
        model_name: Name of the vehicle (e.g., 'Toyota Camry')
    
    Returns:
        Dictionary with vehicle specifications
    """
    data = load_vehicle_data()
    specs_db = data.get('specs', {})
    
    if model_name in specs_db:
        return specs_db[model_name]
    else:
        return {'error': f'Model {model_name} not found'}
```

## 🤖 Add Tools to An Agent 
replace code ที่ไฟล์ sales_agent/agent.py
```python
# agent.py
from google.adk.agents.llm_agent import Agent
from tools.vehicle import (
    get_available_models,
    get_vehicle_specs
)

# สร้าง sales agent สำหรับ dealership
root_agent = Agent(
    model='gemini-2.5-flash',
    name='SalesAgent',
    description='Sales assistant with vehicle lookup and financing tools',
    instruction="""You are an expert automotive sales consultant for a Thai dealership.

You have access to comprehensive tools to help customers:
- Search for available models
- Look up vehicle specifications

If a tool returns a LIST of vehicles: 
Format the result as a human-readable bullet list.""",
    tools=[
        get_available_models,
        get_vehicle_specs
    ]
)
```
## ทดสอบ Run Agent - Multi Tool
![alt text](</assets/img/slide/SalesAgentTools_2.png>)

---
## 🔧 Create Tool - Calculate Monthly Payment and Search Inventory
เพิ่ม function เข้าไปที่ไฟล์ tools/vehicle.py
```python
# tools/vehicle.py
def calculate_monthly_payment(
    price: float,
    down_payment: float,
    loan_term_months: int,
    interest_rate: float
) -> Dict[str, float]:
    """Calculate monthly car payment.
    
    Args:
        price: Vehicle price in THB
        down_payment: Down payment amount
        loan_term_months: Loan duration (36, 60, 84)
        interest_rate: Annual interest rate (e.g., 3.5)
    
    Returns:
        Dictionary with payment calculations
    """
    monthly_rate = interest_rate / 100 / 12
    principal = price - down_payment
    
    if monthly_rate == 0:
        monthly_payment = principal / loan_term_months
    else:
        monthly_payment = principal * monthly_rate * (1 + monthly_rate) ** loan_term_months / \
                         ((1 + monthly_rate) ** loan_term_months - 1)
    
    total_paid = monthly_payment * loan_term_months
    total_interest = total_paid - principal
    
    return {
        'monthly_payment': round(monthly_payment, 2),
        'total_amount': round(total_paid, 2),
        'total_interest': round(total_interest, 2),
        'loan_term_months': loan_term_months
    }

def search_inventory(
    model: Optional[str] = None,
    color: Optional[str] = None,
    max_price: Optional[float] = None
) -> Dict[str, Any]:
    """Search vehicle inventory.
    
    Args:
        model: Vehicle model to search
        color: Optional color filter
        max_price: Optional max price filter (THB)
    
    Returns:
        List of matching vehicles
    """
    data = load_vehicle_data()
    inventory = data.get('inventory', [])
    
    results = inventory
    
    # Filter by model
    if model:
        results = [v for v in results if v['model'].lower() == model.lower()]
    
    # Filter by color if provided
    if color:
        results = [v for v in results if v['color'].lower() == color.lower()]
    
    # Filter by price if provided
    if max_price:
        results = [v for v in results if v['price'] <= max_price]
    
    return {'count': len(results), 'vehicles': results}
```
## Add Tools to An Agent
replace code ที่ไฟล์ sales_agent/agent.py
```python
# agent.py
from google.adk.agents.llm_agent import Agent
from tools.vehicle import (
    get_available_models,
    get_vehicle_specs,
    calculate_monthly_payment,
    search_inventory
)

# สร้าง sales agent สำหรับ dealership
root_agent = Agent(
    model='gemini-2.5-flash',
    name='SalesAgent',
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
Help customers find the perfect vehicle based on their needs and budget.""",
    tools=[
        get_available_models,
        get_vehicle_specs,
        calculate_monthly_payment,
        search_inventory
    ]
)
```
![alt text](</assets/img/slide/SalesAgentTools_3.png>)
---


### How Agent Decides to Use Tools

Google ADK agent automatically:
1. **Analyzes** customer message
2. **Determines** if any tool matches the request
3. **Calls** appropriate tool with parameters
4. **Formats** tool result into response
5. **Responds** to customer

ตัวอย่าง execution flow:

```
Customer: "Toyota Camry ราคาเท่าไหร่ครับ และผ่อนเดือนละเท่าไหร่"
              ↓
Agent analyzes request
              ↓
Decides to use: search_inventory() + calculate_monthly_payment()
              ↓
Calls: search_inventory(model='Toyota Camry')
               → Returns: price = ฿1,299,000
              ↓
Calls: calculate_monthly_payment(
    price=1299000,
    down_payment=300000,
    loan_term_months=60,
    interest_rate=3.5
)
               → Returns: monthly_payment = ฿20,500
              ↓
Agent formats response:
"Toyota Camry อยู่ในสต็อก ราคา ฿1,299,000 ฿
สำหรับการผ่อนช่วงเวลา 60 เดือน ด้วย ฿300,000 ดาวน์
จะเป็นประมาณ ฿20,500 ต่อเดือน"
```

---

## 💡 Best Practices for Tools

1. **Clear Names & Descriptions**: Tool names ต้องชัดเจน ว่าทำอะไร
2. **Proper Type Hints**: ทุก parameter และ return ต้องมี type
3. **Useful Docstrings**: Docstring อธิบายให้ AI เข้าใจ
4. **Error Handling**: Return meaningful error messages
5. **Real Returns**: ส่วนใหญ่ return dict เป็น standard

---

## 🎯 Key Takeaways

1. ✅ Tools เป็น Python functions ที่ agent เรียกใช้
2. ✅ Type hints บ้านเป็นสิ่งจำเป็น
3. ✅ Docstrings ช่วยให้ agent เข้าใจ
4. ✅ Agent decide automatically เมื่อใช้ tool
5. ✅ ใช้ tools เพื่อให้ agent มีความจำเพาะและแม่นยำ

