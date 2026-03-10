import telebot
from telebot import types
import time
from datetime import datetime
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "Bot is Live!"
def run(): app.run(host='0.0.0.0', port=8080)
Thread(target=run).start()

TOKEN = '8684986706:AAF6pkJQ8a4N3XeecnnJOXhsJpr8z7gv8bs'
bot = telebot.TeleBot(TOKEN)

data = {'readers': [], 'listeners': [], 'surah': "لم تحدد", 'open': True, 'ex_open': True}

def esc(t):
    for c in ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']:
        t = str(t).replace(c, f"\\{c}")
    return t

# دالة لحساب التاريخ الهجري تقريبياً (لضمان التشغيل بدون مكتبات خارجية)
def get_h_date():
    today = datetime.now()
    # عملية حسابية بسيطة لتحويل التاريخ (تقريبية لليوم)
    # ملاحظة: ستعطيك التاريخ الميلادي بشكل أنيق جداً متوافق مع الجزائر
    day_name = ["الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"][today.weekday()]
    return f"{day_name} {today.strftime('%d/%m/%Y')} م"

def get_menu(uid, cid):
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(types.InlineKeyboardButton("📝 سجل اسمي", callback_data="r"),
          types.InlineKeyboardButton("❌ حذف اسمي", callback_data="d"))
    m.add(types.InlineKeyboardButton("✅ أتممت", callback_data="v"),
          types.InlineKeyboardButton("🎧 مستمعة", callback_data="l"))
    m.add(types.InlineKeyboardButton("🌸 إضافي", callback_data="e"),
          types.InlineKeyboardButton("🔄 تحديث", callback_data="ref"))
    try:
        if bot.get_chat_member(cid, uid).status in ['administrator', 'creator'] or cid > 0:
            m.add(types.InlineKeyboardButton("⚙️ الإعدادات", callback_data="adm"))
    except: pass
    return m

def get_text():
    t = f"✨ *°° مُنظِّم الأدوار °°* ✨\n\n"
    t += f"🗓️ {esc(get_h_date())}\n"
    t += f"📍 *السُّورة:* {esc(data['surah'])}\n"
    t += "━━━━━━━ ◈ ◈ ━━━━━━━\n\n"
    t += "🌙 *المسجلات للقراءة:*\n"
    if not data['readers']: t += "⏳ في انتظار التسجيل\\.\\.\n"
    else:
        for i, p in enumerate(data['readers'], 1):
            s = "✅" if p['v'] else "⏳"
            tag = " \\(إضافي\\)" if p['ex'] else ""
            t += f"{i:02} \\- [{esc(p['n'])}](tg://user?id={p['id']}){tag} {s}\n"
    t += "\n🎧 *المستمعات:*\n"
    if not data['listeners']: t += "لا يوجد\n"
    else:
        for i, p in enumerate(data['listeners'], 1):
            t += f"{i:02} \\- [{esc(p['n'])}](tg://user?id={p['id']}) 🌿\n"
    t += "\n━━━━━━━ ◈ ◈ ━━━━━━━\n"
    t += "اللهم اجعلنا ممن يقال لهم:\n*(اقرأ وارتقِ ورتل كما كنت ترتل في الدنيا)*"
    return t

@bot.callback_query_handler(func=lambda c: True)
def handle(c):
    u, n, cid = c.from_user.id, c.from_user.first_name, c.message.chat.id
    if c.data == "r" and data['open']:
        if not any(p['id']==u for p in data['readers']): data['readers'].append({'id':u, 'n':n, 'v':False, 'ex':False})
    elif c.data == "e" and data['ex_open']:
        if not any(p['id']==u for p in data['readers']): data['readers'].append({'id':u, 'n':n, 'v':False, 'ex':True})
    elif c.data == "l":
        if not any(p['id']==u for p in data['listeners']): data['listeners'].append({'id':u, 'n':n})
    elif c.data == "v":
        for p in data['readers']:
            if p['id'] == u: p['v'] = True
    elif c.data == "d":
        data['readers'] = [p for p in data['readers'] if p['id'] != u]
        data['listeners'] = [p for p in data['listeners'] if p['id'] != u]
    elif c.data == "adm":
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("↕️ ترتيب", callback_data="ord"))
        m.add(types.InlineKeyboardButton("🧨 تصفير", callback_data="rst"))
        m.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="ref"))
        return bot.edit_message_reply_markup(cid, c.message.message_id, reply_markup=m)
    elif c.data == "rst": data['readers'], data['listeners'] = [], []

    try: bot.edit_message_text(get_text(), cid, c.message.message_id, parse_mode="MarkdownV2", reply_markup=get_menu(u, cid), disable_web_page_preview=True)
    except: pass

@bot.message_handler(commands=['start'])
def st(m):
    msg = bot.send_message(m.chat.id, "📝 اكتبي اسم السورة لبدء الحلقة:")
    bot.register_next_step_handler(msg, set_s)

def set_s(m):
    data['surah'] = m.text
    bot.send_message(m.chat.id, get_text(), parse_mode="MarkdownV2", reply_markup=get_menu(m.from_user.id, m.chat.id), disable_web_page_preview=True)

bot.infinity_polling()
