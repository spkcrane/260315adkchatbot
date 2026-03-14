![alt text](</assets/img/slide/TechnicalTeam.png>)

## ปรับ Technical Agent ให้เป็น Parallel Agent

### เพิ่ม import ParallelAgent ที่ด้านบนสุดของไฟล์
```python
# technical_agent/agent.py
from google.adk.agents.parallel_agent import ParallelAgent
```

## เพิ่ม Agent ผู้เชี่ยวชาญ ที่ไฟล์ technical_agent/agent.py

### Engine Agent
```python
engine_agent = Agent(
    name="EngineDiagnosticAgent",
    model="gemini-2.5-flash",
    description="Diagnoses engine-related vehicle problems",
    output_key="diagnostics_engine",
    instruction="""
You are an automotive engine diagnostic specialist.

Analyze the customer's symptoms and determine if they are related to the engine system.

Examples of engine-related symptoms:
- engine warning light
- engine misfire
- rough idle
- loss of power
- overheating

If the issue is likely related to the engine:
Provide a diagnosis and recommended service.

If the symptom is unrelated to the engine,
state that the engine is unlikely the cause.

"""
)
```

### Break Agent
```python
brake_agent = Agent(
    name="BrakeDiagnosticAgent",
    model="gemini-2.5-flash",
    description="Diagnoses braking system issues",
    output_key="diagnostics_brake",
    instruction="""
You are a brake system diagnostic specialist.

Analyze the vehicle symptoms and determine if they are related to the braking system.

Common brake issues:
- squeaking noise when braking
- grinding sound
- vibration when braking
- reduced braking performance


"""
)
```
### Suspension Agent
```python
suspension_agent = Agent(
    name="SuspensionDiagnosticAgent",
    model="gemini-2.5-flash",
    description="Diagnoses suspension and chassis issues",
    output_key="diagnostics_suspension",
    instruction="""
You are a suspension system specialist.

Analyze whether the symptoms relate to suspension components.

Common suspension symptoms:
- car bouncing excessively
- knocking sounds on bumps
- uneven ride
- steering instability

"""
)
```

### Tire Agent
```python

tire_agent = Agent(
    name="TireDiagnosticAgent",
    model="gemini-2.5-flash",
    description="Diagnoses tire-related issues",
    output_key="diagnostics_tire",
    instruction="""
You are a tire and wheel specialist.

Determine if the symptoms relate to tires or wheel balance.

Common tire symptoms:
- vibration at high speed
- uneven tire wear
- low tire pressure warning
- pulling to one side

"""
)
```

## เปลี่ยน Technical Agent เป็น Parallel Agent
```python
technical_agent = ParallelAgent(
    name="TechnicalParallelDiagnostics",
    description="Coordinates parallel diagnostics and synthesizes the results.",
    sub_agents=[
        engine_agent,
        brake_agent,
        suspension_agent,
        tire_agent
    ]
)
```