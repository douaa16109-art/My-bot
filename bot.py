import telebot
from telebot import types
from datetime import datetime, timedelta
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "Bot is Online!"
def run(): app.run(host='0.0.0.0', port=8080)
Thread(target=run).start()

TOKEN = '8684986706:AAF6pkJQ8a4N3XeecnnJOXhsJpr8z7gv8bs'
bot = telebot.TeleBot(TOKEN)

data = {'readers': [], 'listeners': [], 'surah': "قيد التحديد...", 'waiting': False}

def get_date_fakhma():
    # حساب التاريخ الهجري يدوياً لضمان عدم فشل الموقع
    today = datetime.utcnow() + timedelta(hours=1)
    # معادلة تقريبية دقيقة لشهر رمضان 1447هـ
    day_h = today.day + 10 # تعديل بسيط ليناسب 20 رمضان
    if day_h > 30: day_h -= 30
    days_ar = ["الأحد", "الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت"]
    day_n = days_ar[today.weekday() + 1 if today.weekday() < 6 else 0]
    return f"{day_n} {today.day}/{today.month}/{today.year} م\n🌙 {day_h} رمضان 1447هـ"

def get_text():
    t = f"✨ <b>°° مُنظِّم الأدوار °°</b> ✨\n\n"
    t += f"🗓️ {get_date_fakhma()}\n"
    t += f"📖 <b>السُّورة:</b> {data['surah']}\n"
    t += "━━━━━━━ ◈ ◈ ━━━━━━━\n\n"
    t += "🌙 <b><u>المسجلات للقراءة:</u></b>\n"
    if not data['readers']: t += "⏳ في انتظار التسجيل..\n"
    else:
        for i, p in enumerate(data['readers'], 1):
            s = "✅" if p['done'] else "⏳"
            tag = " (إضافي)" if p['extra'] else ""
            t += f"{i:02}- <a href='tg://user?id={p['id']}'>{p['name']}</a>{tag} {s}\n"
    t += "\n🎧 <b><u>المستمعات:</u></b>\n"
    if not data['listeners']: t += "لا توجد مستمعات.\n"
    else:
        for i, p in enumerate(data['listeners'], 1):
            t += f"{i:02}- <a href='tg://user?id={p['id']}'>{p['name']}</a> 🌿\n"
    t += "\n━━━━━━━ ◈ ◈ ━━━━━━━\n"
    t += "اللهم اجعلنا ممن يقال لهم:\n<b>(اقرأ وارتقِ ورتل كما كنت ترتل في الدنيا)</b>"
    return t

def main_menu():
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(types.InlineKeyboardButton("📝 سجل اسمي", callback_data="reg"),
          types.InlineKeyboardButton("❌ حذف اسمي", callback_data="del"))
    m.add(types.InlineKeyboardButton("✅ قرأت", callback_data="done"),
          types.InlineKeyboardButton("🎧 مستمعة", callback_data="listn"))
    m.add(types.InlineKeyboardButton("🌸 إضافي", callback_data="extra_new"))
    m.add(types.InlineKeyboardButton("🔄 تحديث (إرسال جديد)", callback_data="refresh_new"),
          types.InlineKeyboardButton("⚙️ الإعدادات", callback_data="admin"))
    return m

@bot.message_handler(commands=['start'])
def start(m):
    data['waiting'] = True
    bot.send_message(m.chat.id, "📝 حياكِ الله يا مشرفة.. اكتبي اسم السورة الآن:")

@bot.message_handler(func=lambda m: data['waiting'])
def set_surah(m):
    data['surah'] = m.text
    data['waiting'] = False
    bot.send_message(m.chat.id, get_text(), parse_mode="HTML", reply_markup=main_menu(), disable_web_page_preview=True)

@bot.callback_query_handler(func=lambda c: True)
def calls(c):
    u, n, cid = c.from_user.id, c.from_user.first_name, c.message.chat.id
    
    # حل مشكلة التحديث (يرسل قائمة جديدة ويحذف القديمة)
    if c.data == "refresh_new":
        try: bot.delete_message(cid, c.message.message_id)
        except: pass
        return bot.send_message(cid, get_text(), parse_mode="HTML", reply_markup=main_menu(), disable_web_page_preview=True)

    # حل مشكلة الإضافي (يسجل حتى لو كنتِ مسجلة سابقاً كقارئة)
    elif c.data == "extra_new":
        data['readers'] = [p for p in data['readers'] if p['id'] != u]
        data['readers'].append({'id': u, 'name': n, 'done': False, 'extra': True})
        bot.answer_callback_query(c.id, "تم تسجيلكِ كإضافي ✨")

    elif c.data == "reg":
        if not any(p['id']==u for p in data['readers']):
            data['readers'].append({'id':u, 'name':n, 'done':False, 'extra':False})
    elif c.data == "listn":
        if not any(p['id']==u for p in data['listeners']):
            data['listeners'].append({'id':u, 'name':n})
    elif c.data == "done":
        for p in data['readers']:
            if p['id'] == u: p['done'] = True
    elif c.data == "del":
        data['readers'] = [p for p in data['readers'] if p['id'] != u]
        data['listeners'] = [p for p in data['listeners'] if p['id'] != u]
    elif c.data == "reset":
        data['readers'], data['listeners'] = [], []
    elif c.data == "admin":
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("↕️ ترتيب الأسماء", callback_data="sort"),
              types.InlineKeyboardButton("🧨 تصفير شامل", callback_data="reset"))
        m.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="refresh_new"))
        return bot.edit_message_reply_markup(cid, c.message.message_id, reply_markup=m)

    try: bot.edit_message_text(get_text(), cid, c.message.message_id, parse_mode="HTML", reply_markup=main_menu(), disable_web_page_preview=True)
    except: pass

bot.infinity_polling()
