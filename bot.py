import telebot
from telebot import types
from datetime import datetime
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "Bot is Alive!"
def run(): app.run(host='0.0.0.0', port=8080)
Thread(target=run).start()

TOKEN = '8684986706:AAF6pkJQ8a4N3XeecnnJOXhsJpr8z7gv8bs'
bot = telebot.TeleBot(TOKEN)

# بيانات الحلقة
data = {'readers': [], 'surah': "قيد التحديد...", 'waiting': False}

def get_text():
    # توقيت الجزائر التقريبي
    d = datetime.now().strftime("%d/%m/%Y")
    t = f"✨ <b>°° مُنظِّم الأدوار °°</b> ✨\n\n"
    t += f"🗓️ <b>التاريخ:</b> {d} م\n"
    t += f"📖 <b>السُّورة:</b> {data['surah']}\n"
    t += "━━━━━━━ ◈ ◈ ━━━━━━━\n\n"
    
    t += "🌙 <b>المسجلات للقراءة:</b>\n"
    if not data['readers']:
        t += "⏳ في انتظار تسجيل الأسماء..\n"
    else:
        for i, p in enumerate(data['readers'], 1):
            s = "✅" if p['done'] else "⏳"
            tag = " (إضافي)" if p['extra'] else ""
            t += f"{i:02} - <a href='tg://user?id={p['id']}'>{p['name']}</a>{tag} {s}\n"
            
    t += "\n━━━━━━━ ◈ ◈ ━━━━━━━\n"
    t += "اللهم اجعلنا ممن يقال لهم:\n<b>(اقرأ وارتقِ ورتل كما كنت ترتل في الدنيا)</b>"
    return t

@bot.message_handler(commands=['start'])
def start(m):
    data['waiting'] = True
    bot.send_message(m.chat.id, "📝 حياكِ الله يا مشرفة.. اكتبي اسم السورة الآن:")

@bot.message_handler(func=lambda m: data['waiting'])
def set_surah(m):
    data['surah'] = m.text
    data['waiting'] = False
    m_key = types.InlineKeyboardMarkup(row_width=2)
    m_key.add(types.InlineKeyboardButton("📝 سجل اسمي", callback_data="r"),
              types.InlineKeyboardButton("❌ حذف اسمي", callback_data="del"))
    m_key.add(types.InlineKeyboardButton("✅ قرأت", callback_data="done"),
              types.InlineKeyboardButton("🎧 مستمعة", callback_data="r")) # المستمعة تسجل كقارئة للتبسيط حالياً
    m_key.add(types.InlineKeyboardButton("🌸 إضافي", callback_data="e"),
              types.InlineKeyboardButton("🔄 تحديث", callback_data="ref"))
    m_key.add(types.InlineKeyboardButton("🧨 تصفير", callback_data="reset"))
    bot.send_message(m.chat.id, get_text(), parse_mode="HTML", reply_markup=m_key)

@bot.callback_query_handler(func=lambda c: True)
def calls(c):
    u, n, cid = c.from_user.id, c.from_user.first_name, c.message.chat.id
    if c.data == "r" and not any(p['id']==u for p in data['readers']):
        data['readers'].append({'id':u, 'name':n, 'done':False, 'extra':False})
    elif c.data == "e" and not any(p['id']==u for p in data['readers']):
        data['readers'].append({'id':u, 'name':n, 'done':False, 'extra':True})
    elif c.data == "done":
        for p in data['readers']:
            if p['id'] == u: p['done'] = True
    elif c.data == "del":
        data['readers'] = [p for p in data['readers'] if p['id'] != u]
    elif c.data == "reset":
        data['readers'] = []
    
    m_key = types.InlineKeyboardMarkup(row_width=2)
    m_key.add(types.InlineKeyboardButton("📝 سجل اسمي", callback_data="r"),
              types.InlineKeyboardButton("❌ حذف اسمي", callback_data="del"))
    m_key.add(types.InlineKeyboardButton("✅ قرأت", callback_data="done"),
              types.InlineKeyboardButton("🌸 إضافي", callback_data="e"))
    m_key.add(types.InlineKeyboardButton("🔄 تحديث", callback_data="ref"),
              types.InlineKeyboardButton("🧨 تصفير", callback_data="reset"))

    try:
        bot.edit_message_text(get_text(), cid, c.message.message_id, parse_mode="HTML", reply_markup=m_key, disable_web_page_preview=True)
    except: pass

bot.infinity_polling()
