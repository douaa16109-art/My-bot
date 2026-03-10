import telebot
from telebot import types
import time
from datetime import datetime
from hijri_converter import Gregorian
from flask import Flask
from threading import Thread

# سيرفر لضمان بقاء البوت أونلاين (أخضر)
app = Flask('')
@app.route('/')
def home(): return "Bot is Online and Beautiful!"
def run(): app.run(host='0.0.0.0', port=8080)
Thread(target=run).start()

TOKEN = '8684986706:AAF6pkJQ8a4N3XeecnnJOXhsJpr8z7gv8bs'
bot = telebot.TeleBot(TOKEN)

# قاعدة البيانات
data = {
    'readers': [], # تشمل القارئات والإضافي
    'listeners': [], 
    'surah': "قيد التحديد...",
    'is_open': True, # قفل القائمة كاملة
    'extra_open': True # قفل الإضافي فقط
}

# دالة تنظيف النص لحماية البوت من التعليق
def esc(t):
    for c in ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']:
        t = str(t).replace(c, f"\\{c}")
    return t

# حساب التاريخ الهجري (محاكاة توقيت الجزائر)
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
    
    # صلاحيات المشرفات
    try:
        status = bot.get_chat_member(cid, uid).status
        if status in ['administrator', 'creator'] or cid > 0:
            m.add(types.InlineKeyboardButton("⚙️ إعدادات المشرفات", callback_data="admin"))
    except: pass
    return m

def get_text():
    t = f"✨ *°° مُنظِّم الأدوار °°* ✨\n\n"
    t += f"🗓️ {esc(get_date())}\n"
    t += f"📖 *السُّورة:* {esc(data['surah'])}\n"
    t += "━━━━━━━ ◈ ◈ ━━━━━━━\n\n"
    
    t += "🌙 *المسجلات للقراءة:*\n"
    if not data['readers']: t += "لا توجد مسجلات حالياً\\.\\.\n"
    else:
        for i, p in enumerate(data['readers'], 1):
            status = "✅" if p['done'] else "⏳"
            tag = " \\(إضافي\\)" if p['is_extra'] else ""
            t += f"{i:02} \\- [{esc(p['name'])}](tg://user?id={p['id']}){tag} {status}\n"
            
    t += "\n🎧 *المستمعات:*\n"
    if not data['listeners']: t += "لا توجد مستمعات\\.\n"
    else:
        for i, p in enumerate(data['listeners'], 1):
            t += f"{i:02} \\- [{esc(p['name'])}](tg://user?id={p['id']}) 🌿\n"

    t += "\n━━━━━━━ ◈ ◈ ━━━━━━━\n"
    t += "اللهم اجعلنا ممن يقال لهم:\n*(اقرأ وارتقِ ورتل كما كنت ترتل في الدنيا)*"
    return t

@bot.callback_query_handler(func=lambda c: True)
def handle(c):
    u, n, cid = c.from_user.id, c.from_user.first_name, c.message.chat.id
    
    if c.data == "reg_r":
        if not data['is_open']: return bot.answer_callback_query(c.id, "❌ القائمة مغلقة حالياً")
        if not any(p['id']==u for p in data['readers']):
            data['readers'].append({'id':u, 'name':n, 'done':False, 'is_extra':False})
    
    elif c.data == "reg_e":
        if not data['extra_open']: return bot.answer_callback_query(c.id, "❌ التسجيل الإضافي مغلق")
        if not any(p['id']==u for p in data['readers']):
            data['readers'].append({'id':u, 'name':n, 'done':False, 'is_extra':True})

    elif c.data == "reg_l":
        if not any(p['id']==u for p in data['listeners']):
            data['listeners'].append({'id':u, 'name':n})

    elif c.data == "done":
        for p in data['readers']:
            if p['id'] == u: p['done'] = True
            
    elif c.data == "del":
        data['readers'] = [p for p in data['readers'] if p['id'] != u]
        data['listeners'] = [p for p in data['listeners'] if p['id'] != u]

    elif c.data == "admin":
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("↕️ رفع/خفض الأسماء", callback_data="ord_m"))
        st_txt = "🔒 قفل القائمة" if data['is_open'] else "🔓 فتح القائمة"
        ex_txt = "🔒 قفل الإضافي" if data['extra_open'] else "🔓 فتح الإضافي"
        m.add(types.InlineKeyboardButton(st_txt, callback_data="tog_p"),
              types.InlineKeyboardButton(ex_txt, callback_data="tog_e"))
        m.add(types.InlineKeyboardButton("🧨 تصفير شامل", callback_data="reset"))
        m.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="refresh"))
        return bot.edit_message_reply_markup(cid, c.message.message_id, reply_markup=m)

    # نظام الرفع والخفض
    elif c.data == "ord_m":
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
        m.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="ord_m"))
        return bot.edit_message_reply_markup(cid, c.message.message_id, reply_markup=m)

    elif c.data.startswith("mv:"):
        _, idx, dr = c.data.split(":")
        idx = int(idx)
        lst = data['readers']
        if dr=="up" and idx>0: lst[idx], lst[idx-1] = lst[idx-1], lst[idx]
        elif dr=="down" and idx<len(lst)-1: lst[idx], lst[idx+1] = lst[idx+1], lst[idx]
        bot.answer_callback_query(c.id, "تم التعديل ✅")
        return handle(types.CallbackQuery(c.id, c.from_user, c.message, c.chat_instance, "ord_m"))

    elif c.data == "tog_p": data['is_open'] = not data['is_open']
    elif c.data == "tog_e": data['extra_open'] = not data['extra_open']
    elif c.data == "reset": data['readers'], data['listeners'] = [], []

    try:
        bot.edit_message_text(get_text(), cid, c.message.message_id, parse_mode="MarkdownV2", reply_markup=build_menu(u, cid), disable_web_page_preview=True)
    except: pass

@bot.message_handler(commands=['start'])
def start_cmd(m):
    # السؤال عن السورة أولاً كما طلبتِ
    msg = bot.send_message(m.chat.id, "📝 حياكِ الله يا مشرفة.. يرجى كتابة اسم السورة لبدء القائمة:")
    bot.register_next_step_handler(msg, set_surah_and_show)

def set_surah_and_show(m):
    data['surah'] = m.text
    bot.send_message(m.chat.id, get_text(), parse_mode="MarkdownV2", reply_markup=build_menu(m.from_user.id, m.chat.id), disable_web_page_preview=True)

bot.infinity_polling()
