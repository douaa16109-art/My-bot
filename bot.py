import telebot
from telebot import types
import time
from flask import Flask
from threading import Thread

# --- سيرفر Flask للبقاء حياً ---
app = Flask('')
@app.route('/')
def home(): return "Bot is Online!"

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

# --- إعدادات البوت ---
TOKEN = '8753124430:AAHjTw4-KRaNUSE5OznIwMjzFaXN6ll2FIM'
bot = telebot.TeleBot(TOKEN, threaded=True) # تفعيل المسارات المتعددة للسرعة

# ذاكرة تخزين مؤقتة
data = {
    'readers': [], 
    'listeners': [], 
    'extra_roles': [], 
    'is_open': True, 
    'extra_locked': False, 
    'current_surah': "لم تحدد"
}

def get_user_rank(chat_id, user_id):
    try:
        if chat_id > 0: return True
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ['administrator', 'creator']
    except: return False

def build_menu(chat_id, user_id):
    m = types.InlineKeyboardMarkup(row_width=2)
    is_admin = get_user_rank(chat_id, user_id)
    
    # أزرار المستخدمين (أفقية لتقليل طول القائمة)
    m.add(types.InlineKeyboardButton("📖 تسجيل قارئة", callback_data="reg_read"),
          types.InlineKeyboardButton("🎧 تسجيل مستمعة", callback_data="reg_listen"))
    
    # زر الإضافي (مستقل وواضح)
    extra_txt = "🌿 تفعيل الإضافي" if not data['extra_locked'] else "🌿 الإضافي (مغلق)"
    m.add(types.InlineKeyboardButton(extra_txt, callback_data="reg_extra"))
    
    m.add(types.InlineKeyboardButton("✅ أتممت", callback_data="set_done"),
          types.InlineKeyboardButton("🗑️ حذف اسمي", callback_data="user_del"))

    if is_admin:
        m.add(types.InlineKeyboardButton("🔄 تحديث القائمة", callback_data="refresh
