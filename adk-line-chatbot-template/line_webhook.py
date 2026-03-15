import asyncio
import os
import requests as http_requests
from dotenv import load_dotenv
from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
    ImageMessageContent,
    StickerMessageContent,
)
# TODO: เปลี่ยน import path ให้ตรงกับชื่อ pipeline package ของคุณ
from my_pipeline.agent import root_agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part

load_dotenv()

app = Flask(__name__)

CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("CHANNEL_SECRET")

if not CHANNEL_ACCESS_TOKEN or CHANNEL_ACCESS_TOKEN == "your_line_access_token":
    print("WARNING: CHANNEL_ACCESS_TOKEN is not configured. LINE webhook will not work.")
if not CHANNEL_SECRET or CHANNEL_SECRET == "your_line_channel_secret":
    print("WARNING: CHANNEL_SECRET is not configured. LINE webhook will not work.")

# TODO: เปลี่ยน APP_NAME ให้ตรงกับ project ของคุณ
APP_NAME = "my_lead_app"
session_service = InMemorySessionService()

runner = Runner(
    agent=root_agent,
    app_name=APP_NAME,
    session_service=session_service,
)

user_sessions = {}


def push_message(user_id: str, text: str):
    """Fallback: send a push message when reply token has expired."""
    try:
        resp = http_requests.post(
            "https://api.line.me/v2/bot/message/push",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
            },
            json={"to": user_id, "messages": [{"type": "text", "text": text}]},
            timeout=10,
        )
        if resp.status_code == 200:
            print(f"[PUSH] fallback message sent to {user_id}")
        else:
            print(f"[PUSH] failed: {resp.status_code} {resp.text[:100]}")
    except Exception as e:
        print(f"[PUSH] error: {e}")


def show_loading_animation(chat_id: str, seconds: int = 20):
    """Show LINE loading animation (typing dots) in 1:1 chat.
    Only works in 1:1 chats. Silently ignored for groups/rooms."""
    try:
        resp = http_requests.post(
            "https://api.line.me/v2/bot/chat/loading/start",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
            },
            json={"chatId": chat_id, "loadingSeconds": seconds},
            timeout=5,
        )
        if resp.status_code in (200, 202):
            print(f"[LOADING] animation started for {chat_id}")
        else:
            print(f"[LOADING] failed: {resp.status_code} {resp.text[:100]}")
    except Exception as e:
        print(f"[LOADING] error: {e}")


def get_agent_response(user_message=None, user_id=None):
    if user_id not in user_sessions:
        session = asyncio.run(
            session_service.create_session(app_name=APP_NAME, user_id=user_id)
        )
        user_sessions[user_id] = session.id

    session_id = user_sessions[user_id]

    parts = [Part(text=user_message)] if user_message else []
    content = Content(role="user", parts=parts)
    events = runner.run(
        user_id=user_id, session_id=session_id, new_message=content
    )

    last_text = None
    for event in events:
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    last_text = part.text

    # TODO: เปลี่ยนข้อความ fallback ตามธุรกิจของคุณ
    return last_text or "ขออภัยค่ะ ระบบขัดข้อง กรุณาลองใหม่อีกครั้งนะคะ"


if CHANNEL_SECRET and CHANNEL_SECRET != "your_line_channel_secret":
    configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
    handler = WebhookHandler(CHANNEL_SECRET)
    api_client = ApiClient(configuration)
    messaging_api = MessagingApi(api_client)

    @app.route("/webhook", methods=["POST"])
    def webhook():
        signature = request.headers.get("X-Line-Signature", "")
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

        return "OK"

    def _handle_event(event, agent_text: str, label: str, fallback: str):
        """Common handler: send agent_text to ADK, reply to LINE."""
        line_user_id = event.source.user_id
        print(f"[IN] {line_user_id}: {label}")
        show_loading_animation(line_user_id)
        try:
            reply_text = get_agent_response(
                user_message=agent_text, user_id=line_user_id
            )
        except Exception as e:
            print(f"[ERROR] Agent error ({label}): {e}")
            reply_text = fallback
        print(f"[OUT] {reply_text[:100]}")
        try:
            messaging_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=reply_text)],
                )
            )
        except Exception as e:
            print(f"[ERROR] Reply failed ({label}, token expired?): {e}")
            push_message(line_user_id, reply_text)

    @handler.add(MessageEvent, message=TextMessageContent)
    def handle_text_message(event):
        _handle_event(
            event,
            agent_text=event.message.text,
            label=event.message.text,
            # TODO: เปลี่ยนข้อความ fallback ตามธุรกิจของคุณ
            fallback="ขออภัยค่ะ ระบบขัดข้องชั่วคราว กรุณาลองใหม่นะคะ",
        )

    @handler.add(MessageEvent, message=ImageMessageContent)
    def handle_image_message(event):
        _handle_event(
            event,
            # TODO: เปลี่ยน synthetic text ถ้าต้องการ
            agent_text="[ลูกค้าส่งรูปภาพ]",
            label="[image]",
            fallback="ขอบคุณสำหรับภาพค่ะ",
        )

    @handler.add(MessageEvent, message=StickerMessageContent)
    def handle_sticker_message(event):
        _handle_event(
            event,
            # TODO: เปลี่ยน synthetic text ถ้าต้องการ
            agent_text="[ลูกค้าส่ง sticker]",
            label="[sticker]",
            fallback="ขอบคุณค่ะ",
        )


@app.route("/", methods=["GET"])
def root():
    # TODO: เปลี่ยนข้อความ status ตาม project ของคุณ
    return {"status": "ok", "message": "My Lead Bot is running"}


if __name__ == "__main__":
    # Note: port 8000 conflicts with 'adk web'. Stop adk web before running this.
    app.run(host="0.0.0.0", port=8000, debug=True)
