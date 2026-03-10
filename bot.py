import telebot
from telebot import types
from datetime import datetime
from hijri_converter import Gregorian
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "Bot is Online and Stable!"
def run(): app.run(host='0.0.0.0', port=8080)
Thread(target=run).start()

TOKEN = '8684986706:AAF6pkJQ8a4N3XeecnnJOXhsJpr8z7gv8bs'
bot = telebot.TeleBot(TOKEN)

data = {
    'readers': [], 'listeners': [], 
    'surah': "قيد التحديد...",
    'is_open': True, 'extra_open': True,
    'waiting_for_surah': False
}

def get_date():
    today = datetime.now()
    h = Gregorian(today.year, today.month, today.day).to_hijri()
    days_ar = ["الأحد", "الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت"]
    day_name = days_ar[today.weekday() + 1 if today.weekday() < 6 else 0]
    months_ar = ["محرم", "صفر", "ربيع الأول", "ربيع الثاني", "جمادى الأولى", "جمادى الآخرة", "رجب", "شعبان", "رمضان", "شوال", "ذو القعدة", "ذو الحجة"]
    return f"{day_name} {h.day} {months_ar[h.month-1]} {h.year}هـ"

def build_menu(uid, cid):
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(types.InlineKeyboardButton("📝 سجل اسمي", callback_data="reg_r"),
          types.InlineKeyboardButton("❌ حذف اسمي", callback_data="del"))
    m.add(types.InlineKeyboardButton("✅ أتممت القراءة", callback_data="done"),
          types.InlineKeyboardButton("🎧 مستمعة", callback_data="reg_l"))
    m.add(types.InlineKeyboardButton("🌸 إضافي", callback_data="reg_e"))
    m.add(types.InlineKeyboardButton("🔄 تحديث القائمة", callback_data="refresh"))
    try:
        status = bot.get_chat_member(cid, uid).status
        if status in ['administrator', 'creator'] or cid > 0:
            m.add(types.InlineKeyboardButton("⚙️ إعدادات المشرفات", callback_data="admin"))
    except: pass
    return m

def get_text():
    # هنا استخدمنا HTML بدلاً من Markdown لضمان عدم حدوث خطأ 400
    t = f"✨ <b>°° مُنظِّم الأدوار °°</b> ✨\n\n"
    t += f"🗓️ {get_date()}\n"
    t += f"📖 <b>السُّورة:</b> {data['surah']}\n"
    t += "━━━━━━━ ◈ ◈ ━━━━━━━\n\n"
    
    t += "🌙 <b>المسجلات للقراءة:</b>\n"
    if not data['readers']: t += "لا توجد مسجلات حالياً..\n"
    else:
        for i, p in enumerate(data['readers'], 1):
            s = "✅" if p['done'] else "⏳"
            tag = " (إضافي)" if p['is_extra'] else ""
            t += f"{i:02} - <a href='tg://user?id={p['id']}'>{p['name']}</a>{tag} {s}\n"
            
    t += "\n🎧 <b>المستمعات:</b>\n"
    if not data['listeners']: t += "لا توجد مستمعات.\n"
    else:
        for i, p in enumerate(data['listeners'], 1):
            t += f"{i:02} - <a href='tg://user?id={p['id']}'>{p['name']}</a> 🌿\n"

    t += "\n━━━━━━━ ◈ ◈ ━━━━━━━\n"
    t += "اللهم اجعلنا ممن يقال لهم:\n<b>(اقرأ وارتقِ ورتل كما كنت ترتل في الدنيا)</b>"
    return t

@bot.message_handler(commands=['start'])
def start_cmd(m):
    data['waiting_for_surah'] = True
    bot.send_message(m.chat.id, "📝 حياكِ الله يا مشرفة.. يرجى كتابة اسم السورة لبدء القائمة:")

@bot.message_handler(func=lambda m: data.get('waiting_for_surah', False))
def handle_surah_input(m):
    data['surah'] = m.text
    data['waiting_for_surah'] = False
    bot.send_message(m.chat.id, get_text(), parse_mode="HTML", reply_markup=build_menu(m.from_user.id, m.chat.id), disable_web_page_preview=True)

@bot.callback_query_handler(func=lambda c: True)
def handle_calls(c):
    u, n, cid = c.from_user.id, c.from_user.first_name, c.message.chat.id
    if c.data == "reg_r":
        if not data['is_open']: return bot.answer_callback_query(c.id, "❌ القائمة مغلقة")
        if not any(p['id']==u for p in data['readers']): data['readers'].append({'id':u, 'name':n, 'done':False, 'is_extra':False})
    elif c.data == "reg_e":
        if not data['extra_open']: return bot.answer_callback_query(c.id, "❌ الإضافي مغلق")
        if not any(p['id']==u for p in data['readers']): data['readers'].append({'id':u, 'name':n, 'done':False, 'is_extra':True})
    elif c.data == "reg_l":
        if not any(p['id']==u for p in data['listeners']): data['listeners'].append({'id':u, 'name':n})
    elif c.data == "done":
        for p in data['readers']:
            if p['id'] == u: p['done'] = True
    elif c.data == "del":
        data['readers'] = [p for p in data['readers'] if p['id'] != u]
        data['listeners'] = [p for p in data['listeners'] if p['id'] != u]
    elif c.data == "admin":
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("🧨 تصفير شامل", callback_data="reset"))
        m.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="refresh"))
        return bot.edit_message_reply_markup(cid, c.message.message_id, reply_markup=m)
    elif c.data == "reset": data['readers'], data['listeners'] = [], []
    
    try:
        bot.edit_message_text(get_text(), cid, c.message.message_id, parse_mode="HTML", reply_markup=build_menu(u, cid), disable_web_page_preview=True)
    except: pass

bot.infinity_polling()
