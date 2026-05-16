import os
import threading
import asyncio
import feedparser
from flask import Flask
from pyrogram import Client, filters

# --- إعداد السيرفر الوهمي (Flask) ---
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Cinema Multi-Source RSS Bot is Running!"

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

app = Client("cinema_news_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# قائمة حفظ المشتركين (أنت) وايديات القنوات إذا ردت تضيفها مستقبلاً
subscribers = set()
sent_news = set()

# 🔥 مصفوفة القنوات والمواقع اللي طلبتها مضافاً لها روابط الـ RSS الدقيقة مالتها
RSS_FEEDS = {
    "What To Watch": "https://www.whattowatch.com/feeds/all",
    "السينما.كوم": "https://elcinema.com/news/rss",
    "Marca (Entertainment)": "https://www.marca.com/en/rss/lifestyle.xml", # قسم اللايف ستايل والترفيه بماركا
    "TheWrap": "https://www.thewrap.com/feed/",
    "Collider": "https://collider.com/feed/",
    "Empire Online": "https://www.empireonline.com/movies/feed/",
    "Vanity Fair": "https://www.vanityfair.com/feed/culture/rss",
    "Deadline (إضافة من عندي)": "https://deadline.com/feed/",
    "Variety (إضافة من عندي)": "https://variety.com/feed/"
}

@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    chat_id = message.chat.id
    subscribers.add(chat_id)
    
    text = (
        f"هلا بيك حسين! 🎬\n\n"
        f"تم ربط البوت بـ {len(RSS_FEEDS)} مواقع عالمية وعربية بنجاح.\n"
        "أي خبر، تريلر، ملصق، أو تجديد ينزل بهذني المواقع راح يوصلك هنا فوراً."
    )
    await message.reply_text(text)

# دالة فحص موقع واحد بشكل منفصل ومستقل
async def check_single_feed(source_name, feed_url):
    try:
        feed = await asyncio.to_thread(feedparser.parse, feed_url)
        # نأخذ آخر خبرين نزلوا بكل موقع بالفحص الحالي حتى نضمن السرعة
        for entry in feed.entries[:2]:
            link = entry.link
            title = entry.title
            
            if link not in sent_news:
                sent_news.add(link)
                
                msg = (
                    f"📰 **المصدر:** #{source_name.replace(' ', '_')}\n\n"
                    f"📌 **العنوان:** {title}\n"
                    f"🔗 **الرابط:** {link}\n"
                )
                
                for user_id in subscribers:
                    try:
                        await app.send_message(user_id, msg)
                    except Exception as e:
                        print(f"Error sending to {user_id}: {e}")
    except Exception as e:
        print(f"Error checking {source_name}: {e}")

# الدالة الأساسية اللي تشغل الفحص لكل المواقع بالتوازي
async def fetch_news_loop():
    while True:
        # نسوي كاسك (Task) لكل موقع حتى يشتغلون كلهم سوه بنفس الثانية وبدون تأخير
        tasks = [check_single_feed(name, url) for name, url in RSS_FEEDS.items()]
        await asyncio.gather(*tasks)
        
        # الفحص يتكرر كل 10 دقائق (وقت ممتاز ومثالي للحصريات وبدون حظر)
        await asyncio.sleep(600)

async def main():
    keep_alive()
    await app.start()
    print("Cinema Multi-Source Bot is Running...")
    
    # تشغيل دوارة الفحص بالخلفية
    asyncio.create_task(fetch_news_loop())
    
    from pyrogram import idle
    await idle()
    await app.stop()

if __name__ == "__main__":
    app.run(main())
    
