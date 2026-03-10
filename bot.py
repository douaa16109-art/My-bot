import telebot
from telebot import types
import time
from datetime import datetime
from flask import Flask
from threading import Thread

# تشغيل السيرفر لضمان بقاء البوت أخضر في UptimeRobot
app = Flask('')
@app.route('/')
def home(): return "Bot is Fully Operational and Green!"
def run(): app.run(host='0.0.0.0', port=8080)
Thread(target=run).start()

TOKEN = '8684986706:AAF6pkJQ8a4N3XeecnnJOXhsJpr8z7gv8bs'
bot = telebot.TeleBot(TOKEN)

# قاعدة بيانات البوت (القارئات، المستمعات، الإضافي، والسورة)
data = {'readers': [], 'listeners': [], 'extra': [], 'surah': "لم تُحدد بعد"}

# دالة حماية النص من أخطاء التليجرام (MarkdownV2)
def esc(t):
    for c in ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']:
        t = t.replace(c, f"\\{c}")
    return t

def get_menu(uid, cid):
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(types.InlineKeyboardButton("📝 سجل اسمي", callback_data="reg_r"),
          types.InlineKeyboardButton("❌ احذف اسمي", callback_data="del"))
    m.add(types.InlineKeyboardButton("✅ قرأت", callback_data="done"),
          types.InlineKeyboardButton("🎧 مستمعة", callback_data="reg_l"))
    m.add(types.InlineKeyboardButton("🌸 معتذرة (إضافي)", callback_data="reg_e"))
    m.add(types.InlineKeyboardButton("🔄 تحديث القائمة", callback_data="refresh"))
    try:
        if bot.get_chat_member(cid, uid).status in ['administrator', 'creator'] or cid > 0:
            m.add(types.InlineKeyboardButton("⚙️ إعدادات المشرفات", callback_data="admin"))
    except: pass
    return m

def get_text():
    day = datetime.now().strftime("%d/%m/%Y")
    t = f"❄️ *بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ* ❄️\n🌿 *مَجْلِسُ تِلَاوَةِ القُرْآنِ الكَرِيمِ* 🌿\n\n"
    t += f"🗓️ {esc(day)} م\n📍 *السُّورَةُ:* {esc(data['surah'])}\n"
    t += "━━━━━━━━━━━━━━\n\n"
    t += "📖 *القارئات:*\n"
    if not data['readers']: t += "⏳ في انتظار التسجيل\\.\\.\n"
    else:
        for i, p in enumerate(data['readers'], 1):
            s = "✅" if p['done'] else "⏳"
            t += f"{i:02} \\- [{esc(p['name'])}](tg://user?id={p['id']}) {s}\n"
    t += "\n✨ *الأدوار الإضافية:*\n"
    for i, p in enumerate(data['extra'], 1):
        t += f"{i:02} \\- [{esc(p['name'])}](tg://user?id={p['id']}) ⭐\n"
    t += "\n🎧 *المستمعات:*\n"
    for i, p in enumerate(data['listeners'], 1):
        t += f"{i:02} \\- [{esc(p['name'])}](tg://user?id={p['id']}) 🌿\n"
    t += "\n━━━━━━━━━━━━━━\n"
    t += "اللهم اجعلنا ممن يقال لهم:\n*(اقرأ وارتقِ ورتل كما كنت ترتل في الدنيا)*"
    return t

@bot.callback_query_handler(func=lambda c: True)
def handle(c):
    u, n, cid = c.from_user.id, c.from_user.first_name, c.message.chat.id
    
    if c.data == "reg_r":
        if not any(p['id']==u for p in data['readers']): data['readers'].append({'id':u, 'n':n, 'name':n, 'done':False})
    elif c.data == "reg_l":
        if not any(p['id']==u for p in data['listeners']): data['listeners'].append({'id':u, 'n':n, 'name':n})
    elif c.data == "reg_e":
        if not any(p['id']==u for p in data['extra']): data['extra'].append({'id':u, 'n':n, 'name':n})
    elif c.data == "done":
        for p in data['readers']:
            if p['id'] == u: p['done'] = True
    elif c.data == "del":
        data['readers'] = [p for p in data['readers'] if p['id'] != u]
        data['listeners'] = [p for p in data['listeners'] if p['id'] != u]
        data['extra'] = [p for p in data['extra'] if p['id'] != u]
    elif c.data == "admin":
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("↕️ رفع/خفض الأسماء", callback_data="ord_m"),
              types.InlineKeyboardButton("✍️ تغيير السورة", callback_data="set_s"))
        m.add(types.InlineKeyboardButton("🧨 تصفير شامل", callback_data="reset"),
              types.InlineKeyboardButton("⬅️ رجوع", callback_data="refresh"))
        return bot.edit_message_reply_markup(cid, c.message.message_id, reply_markup=m)
    
    # --- نظام الرفع والخفض اليدوي ---
    elif c.data == "ord_m":
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("قائمة القارئات", callback_data="list:readers"),
              types.InlineKeyboardButton("الأدوار الإضافية", callback_data="list:extra"))
        m.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="admin"))
        return bot.edit_message_reply_markup(cid, c.message.message_id, reply_markup=m)
    elif c.data.startswith("list:"):
        l_type = c.data.split(":")[1]
        m = types.InlineKeyboardMarkup()
        for i, p in enumerate(data[l_type]):
            m.add(types.InlineKeyboardButton(p['name'], callback_data=f"pk:{l_type}:{i}"))
        m.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="ord_m"))
        return bot.edit_message_reply_markup(cid, c.message.message_id, reply_markup=m)
    elif c.data.startswith("pk:"):
        _, lt, idx = c.data.split(":")
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("🔼 رفع", callback_data=f"mv:{lt}:{idx}:up"),
              types.InlineKeyboardButton("🔽 خفض", callback_data=f"mv:{lt}:{idx}:down"))
        m.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data=f"list:{lt}"))
        return bot.edit_message_reply_markup(cid, c.message.message_id, reply_markup=m)
    elif c.data.startswith("mv:"):
        _, lt, idx, dr = c.data.split(":")
        idx = int(idx)
        lst = data[lt]
        if dr=="up" and idx>0: lst[idx], lst[idx-1] = lst[idx-1], lst[idx]
        elif dr=="down" and idx<len(lst)-1: lst[idx], lst[idx+1] = lst[idx+1], lst[idx]
        bot.answer_callback_query(c.id, "تم التغيير ✅")
        return handle(types.CallbackQuery(c.id, c.from_user, c.message, c.chat_instance, f"list:{lt}"))

    elif c.data == "reset": data['readers'], data['listeners'], data['extra'] = [], [], []
    elif c.data == "set_s": return bot.send_message(cid, "اكتبي اسم السورة الجديدة:")

    try: bot.edit_message_text(get_text(), cid, c.message.message_id, parse_mode="MarkdownV2", reply_markup=get_menu(u, cid), disable_web_page_preview=True)
    except: pass

@bot.message_handler(func=lambda m: True)
def msg_h(m):
    if m.text.startswith('/start'):
        bot.send_message(m.chat.id, get_text(), parse_mode="MarkdownV2", reply_markup=get_menu(m.from_user.id, m.chat.id), disable_web_page_preview=True)
    elif not m.text.startswith('/'):
        data['surah'] = m.text
        bot.reply_to(m, "✅ تم تحديث السورة")

bot.infinity_polling()
