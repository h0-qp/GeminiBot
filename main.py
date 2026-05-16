import os
import threading
import asyncio
from flask import Flask
from pyrogram import Client, filters
from pyrogram.enums import ChatAction
from google import genai # المكتبة الجديدة

# --- إعداد السيرفر الوهمي (Flask) ---
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Gemini Pyrogram Bot is Running!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = threading.Thread(target=run_web)
    t.start()
# ----------------------------------------------

# إعدادات Pyrogram
api_id = 28222279
api_hash = "bf76ce65a3af59f3565f63501800aa14"
bot_token = os.getenv("BOT_TOKEN")

app = Client("gemini_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# إعدادات جيميناي (المكتبة الجديدة)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

# قاموس لحفظ ذاكرة المحادثة لكل مستخدم
user_sessions = {}

@app.on_message(filters.command("start"))
async def start(client, message):
    chat_id = message.chat.id
    
    # بدء جلسة جديدة بالنظام الجديد
    try:
        user_sessions[chat_id] = gemini_client.chats.create(model="gemini-1.5-flash")
        
        text = (
            f"هلا بيك {message.from_user.first_name}! 👋\n\n"
            "أنا بوت ذكاء اصطناعي مدعوم من Gemini. "
            "أكدر أجاوب على أسئلتك، أكتبلك أكواد، وأسولف وياك بأي موضوع.\n\n"
            "تفضل، شنو تحب تسألني اليوم؟"
        )
        await message.reply_text(text)
    except Exception as e:
        print(f"Start Error: {e}")

@app.on_message(filters.text & ~filters.command("start"))
async def handle_message(client, message):
    chat_id = message.chat.id
    
    # التأكد من وجود جلسة
    if chat_id not in user_sessions:
        try:
            user_sessions[chat_id] = gemini_client.chats.create(model="gemini-1.5-flash")
        except Exception as e:
            print(f"Session Error: {e}")
            return
            
    chat_session = user_sessions[chat_id]
    
    # إظهار حالة "يكتب..."
    await client.send_chat_action(chat_id, ChatAction.TYPING)
    
    try:
        # إرسال الرسالة وجلب الرد
        response = await asyncio.to_thread(chat_session.send_message, message.text)
        await message.reply_text(response.text)
    except Exception as e:
        await message.reply_text("عذراً، صار عندي ضغط أو مشكلة بالاتصال. حاول تسألني مرة ثانية! 🔄")
        print(f"API Error: {e}")

if __name__ == "__main__":
    keep_alive() 
    print("Gemini Pyrogram Bot is starting...")
    app.run() 
