## Create LINE OA
[LINE OA Manager](https://manager.line.biz/)

## Copy CHANNEL_SECRET and LINE CHANNEL_ACCESS_TOKEN
[LINE Developers](https://developers.line.biz/)

## เริ่มแก้ไข Code
### Install dependency 
```bash
pip install flask uvicorn line-bot-sdk python-dotenv
```

### สร้างไฟล์สำหรับ LINE Webhook
```bash
touch line_webhook.py
```

### Code สำหรับ LINE Webhook
```python
import asyncio
import base64
import os
from dotenv import load_dotenv
from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    MessagingApiBlob,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
    ImageMessageContent
)
# 🔥 base_agent (entry point ของ agent ทั้งระบบ)
from base_agent.agent import get_agent_response
load_dotenv()

app = Flask(__name__)

CHANNEL_ACCESS_TOKEN = os.getenv('CHANNEL_ACCESS_TOKEN')
CHANNEL_SECRET = os.getenv('CHANNEL_SECRET')

if not CHANNEL_ACCESS_TOKEN or not CHANNEL_SECRET:
    raise ValueError("CHANNEL_ACCESS_TOKEN and CHANNEL_SECRET must be set in .env file")

configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)
api_client = ApiClient(configuration)
messaging_api = MessagingApi(api_client)

@app.route("/", methods=['GET'])
def root():
    return {"status": "ok", "message": "LINE Bot with ADK is running"}

@app.route("/webhook", methods=['POST'])
def webhook():
    signature = request.headers.get('X-Line-Signature', '')
    
    if not signature:
        abort(400, description="Missing X-Line-Signature header")
    
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    except Exception as e:
        app.logger.error(f"Error handling webhook: {e}")
        abort(500)
    
    return 'OK'

@handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event):
    line_user_id = event.source.user_id
    user_message = event.message.text
    try:
        reply_text = get_agent_response(
            user_message=user_message, 
            user_id=line_user_id
        )
    except Exception as e:
        print(f"Error: {e}")
        reply_text = "เกิดข้อผิดพลาดในการประมวลผลครับ"
    messaging_api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[TextMessage(text=reply_text)]
        )
    )
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)

```

### Setup ค่า Config
```bash
export CHANNEL_SECRET="YOUR_CHANNEL_SECRET"
export CHANNEL_ACCESS_TOKEN="YOUR_ACCESS_TOKEN"
```

## ปรับ Base Agent ให้เรียกผ่าน Runner เพื่อใช้กับ LINE Webhook
### Import library ที่จำเป็นสำหรับใช้กับ Runner
เพิ่มเติมส่วน Import และ กำหนดค่า Config 
```python
# base_agent/agent.py
import asyncio
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part
from dotenv import load_dotenv
load_dotenv()

APP_NAME = "memory_automotive_app"
session_service = InMemorySessionService()

```

### เพิ่ม Code สำหรับสร้าง Runner ที่ด้านล่างสุดของไฟล์
```python
# Call Runner
runner = Runner(
    agent=root_agent,
    app_name=APP_NAME,
    session_service=session_service,
)
```
### เพิ่ม function สำหรับ จัดการ Memory และ เรียกใช้งาน Runner และคืนค่าให้ LINE Webhook ที่ด้านล่างสุดของไฟล์
```python
user_sessions = {}
def get_agent_response(user_message=None, user_id=None):
    if user_id not in user_sessions:
        session = asyncio.run(session_service.create_session(app_name=APP_NAME, user_id=user_id))
        user_sessions[user_id] = session.id
    
    session_id = user_sessions[user_id]
    
    parts = [Part(text=user_message)] if user_message else []
    content = Content(role="user", parts=parts)
    events = runner.run(user_id=user_id, session_id=session_id, new_message=content)
    
    for event in events:
        if event.is_final_response():
            return event.content.parts[0].text
    
    return "ขออภัย ระบบขัดข้อง"


```

## ทดสอบ Run ไฟล์ LINE Webhook
```bash
python line_webhook.py
```

## เปิด Tunnel ที่ Port 8000 เพื่อให้ Public 
![alt text](/assets/img/slide/TunnelPort.png)

## Copy link ใส่ใน Webhook URL 
อย่าลืมเปิด Use webhook นะค้าบบ ^^
![alt text](/assets/img/slide/ConfigLINEWebhook.png)

## ทดสอบ Chat ผ่าน LINE
![alt text](/assets/img/slide/TestLINEChat.png)