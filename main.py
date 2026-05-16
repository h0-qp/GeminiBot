import os
import threading
import asyncio
from flask import Flask
from pyrogram import Client, filters
from pyrogram.enums import ChatAction
from google import genai

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

# إعدادات جيميناي
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

# قاموس لحفظ ذاكرة المحادثة لكل مستخدم (نظام الذاكرة اليدوي)
user_sessions = {}

@app.on_message(filters.command("start") & filters.private & ~filters.me)
async def start(client, message):
    chat_id = message.chat.id
    
    # تصفير الذاكرة وبدء مصفوفة جديدة
    user_sessions[chat_id] = []
    
    text = (
        f"هلا بيك {message.from_user.first_name}! 👋\n\n"
        "أنا بوت ذكاء اصطناعي مدعوم من Gemini. "
        "أكدر أجاوب على أسئلتك، أكتبلك أكواد، وأسولف وياك بأي موضوع.\n\n"
        "تفضل، شنو تحب تسألني اليوم؟"
    )
    await message.reply_text(text)

@app.on_message((filters.text | filters.caption) & filters.private & ~filters.command("start") & ~filters.me)
async def handle_message(client, message):
    chat_id = message.chat.id
    
    # استخراج النص الصافي
    user_text = message.text or message.caption
    if not user_text:
        return
    user_text = str(user_text).strip()
    
    # إذا المستخدم ما دايس start، نفتحله ذاكرة جديدة
    if chat_id not in user_sessions:
        user_sessions[chat_id] = []
        
    # 🔥 هنا السر: نضيف رسالتك للذاكرة بصيغة القاموس اللي يقبلها جوجل غصباً عنه
    user_sessions[chat_id].append({'role': 'user', 'parts': [{'text': user_text}]})
    
    await client.send_chat_action(chat_id, ChatAction.TYPING)
    
    try:
        # نرسل الذاكرة كلها مباشرة للمحرك الأساسي بدون تعقيدات
        response = await asyncio.to_thread(
            gemini_client.models.generate_content,
            model='gemini-1.5-flash',
            contents=user_sessions[chat_id]
        )
        
        reply = response.text
        
        # إذا رجع رد، نضيفه للذاكرة حتى البوت يتذكر السياق
        if reply:
            user_sessions[chat_id].append({'role': 'model', 'parts': [{'text': reply}]})
            await message.reply_text(reply)
            
    except Exception as e:
        # إذا صار خطأ، نمسح آخر رسالة دزيتها حتى لا تتخربط الذاكرة
        if len(user_sessions[chat_id]) > 0:
            user_sessions[chat_id].pop()
        await message.reply_text(f"⚠️ خطأ بالاتصال:\n`{str(e)}`")

if __name__ == "__main__":
    keep_alive() 
    print("Gemini Pyrogram Bot is starting...")
    app.run() 
