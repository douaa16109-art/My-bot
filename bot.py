import telebot
from telebot import types
from datetime import datetime
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "Bot is Fully Operational!"
def run(): app.run(host='0.0.0.0', port=8080)
Thread(target=run).start()

TOKEN = '8684986706:AAF6pkJQ8a4N3XeecnnJOXhsJpr8z7gv8bs'
bot = telebot.TeleBot(TOKEN)

# قاعدة البيانات (أضفنا المستمعات وحالة القفل)
data = {
    'readers': [], 
    'listeners': [], 
    'surah': "قيد التحديد...", 
    'waiting': False,
    'open': True,
    'extra_open': True
}

def get_text():
    d = datetime.now().strftime("%d/%m/%Y")
    t = f"✨ <b>°° مُنظِّم الأدوار °°</b> ✨\n\n"
    t += f"🗓️ <b>التاريخ:</b> {d} م\n"
    t += f"📖 <b>السُّورة:</b> {data['surah']}\n"
    t += "━━━━━━━ ◈ ◈ ━━━━━━━\n\n"
    
    t += "🌙 <b>المسجلات للقراءة:</b>\n"
    if not data['readers']: t += "⏳ في انتظار التسجيل..\n"
    else:
        for i, p in enumerate(data['readers'], 1):
            s = "✅" if p['done'] else "⏳"
            tag = " (إضافي)" if p['extra'] else ""
            t += f"{i:02} - <a href='tg://user?id={p['id']}'>{p['name']}</a>{tag} {s}\n"
            
    t += "\n🎧 <b>المستمعات:</b>\n"
    if not data['listeners']: t += "لا توجد مستمعات.\n"
    else:
        for i, p in enumerate(data['listeners'], 1):
            t += f"{i:02} - <a href='tg://user?id={p['id']}'>{p['name']}</a> 🌿\n"

    t += "\n━━━━━━━ ◈ ◈ ━━━━━━━\n"
    t += "اللهم اجعلنا ممن يقال لهم:\n<b>(اقرأ وارتقِ ورتل كما كنت ترتل في الدنيا)</b>"
    return t

def main_menu(uid, cid):
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(types.InlineKeyboardButton("📝 سجل اسمي", callback_data="reg"),
          types.InlineKeyboardButton("❌ حذف اسمي", callback_data="del"))
    m.add(types.InlineKeyboardButton("✅ قرأت", callback_data="done"),
          types.InlineKeyboardButton("🎧 مستمعة", callback_data="listn"))
    m.add(types.InlineKeyboardButton("🌸 إضافي", callback_data="extra"))
    m.add(types.InlineKeyboardButton("🔄 تحديث", callback_data="ref"),
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
    bot.send_message(m.chat.id, get_text(), parse_mode="HTML", reply_markup=main_menu(m.from_user.id, m.chat.id), disable_web_page_preview=True)

@bot.callback_query_handler(func=lambda c: True)
def calls(c):
    u, n, cid = c.from_user.id, c.from_user.first_name, c.message.chat.id
    
    if c.data == "reg":
        if not any(p['id']==u for p in data['readers']):
            data['readers'].append({'id':u, 'name':n, 'done':False, 'extra':False})
    elif c.data == "extra":
        if not any(p['id']==u for p in data['readers']):
            data['readers'].append({'id':u, 'name':n, 'done':False, 'extra':True})
    elif c.data == "listn":
        if not any(p['id']==u for p in data['listeners']):
            data['listeners'].append({'id':u, 'name':n})
    elif c.data == "done":
        for p in data['readers']:
            if p['id'] == u: p['done'] = True
    elif c.data == "del":
        data['readers'] = [p for p in data['readers'] if p['id'] != u]
        data['listeners'] = [p for p in data['listeners'] if p['id'] != u]
    elif c.data == "ref":
        bot.answer_callback_query(c.id, "تم التحديث ✅")
    elif c.data == "reset":
        data['readers'], data['listeners'] = [], []
        bot.answer_callback_query(c.id, "تم التصفير 🧨")
    
    # قائمة الإعدادات (فيها الترتيب والتصفير)
    elif c.data == "admin":
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("↕️ ترتيب الأسماء", callback_data="sort"))
        m.add(types.InlineKeyboardButton("🧨 تصفير شامل", callback_data="reset"))
        m.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="ref"))
        return bot.edit_message_reply_markup(cid, c.message.message_id, reply_markup=m)
    
    elif c.data == "sort":
        m = types.InlineKeyboardMarkup()
        for i, p in enumerate(data['readers']):
            m.add(types.InlineKeyboardButton(p['name'], callback_data=f"pk:{i}"))
        m.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="admin"))
        return bot.edit_message_reply_markup(cid, c.message.message_id, reply_markup=m)
    
    elif c.data.startswith("pk:"):
        idx = c.data.split(":")[1]
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("🔼 رفع", callback_data=f"mv:{idx}:up"),
              types.InlineKeyboardButton("🔽 خفض", callback_data=f"mv:{idx}:down"))
        m.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="sort"))
        return bot.edit_message_reply_markup(cid, c.message.message_id, reply_markup=m)

    elif c.data.startswith("mv:"):
        _, idx, dr = c.data.split(":")
        idx = int(idx)
        l = data['readers']
        if dr=="up" and idx>0: l[idx], l[idx-1] = l[idx-1], l[idx]
        elif dr=="down" and idx<len(l)-1: l[idx], l[idx+1] = l[idx+1], l[idx]
        return calls(types.CallbackQuery(c.id, c.from_user, c.message, c.chat_instance, "sort"))

    try:
        bot.edit_message_text(get_text(), cid, c.message.message_id, parse_mode="HTML", reply_markup=main_menu(u, cid), disable_web_page_preview=True)
    except: pass

bot.infinity_polling()
