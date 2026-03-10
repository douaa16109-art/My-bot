import telebot
from telebot import types
from datetime import datetime, timedelta
from hijri_converter import Gregorian
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "Bot is Fully Operational!"
def run(): app.run(host='0.0.0.0', port=8080)
Thread(target=run).start()

TOKEN = '8684986706:AAF6pkJQ8a4N3XeecnnJOXhsJpr8z7gv8bs'
bot = telebot.TeleBot(TOKEN)

# قاعدة البيانات
data = {
    'readers': [], 
    'listeners': [], 
    'surah': "قيد التحديد...", 
    'waiting': False
}

def get_hijri_date():
    try:
        # توقيت الجزائر (GMT+1)
        dz_time = datetime.utcnow() + timedelta(hours=1)
        h = Gregorian(dz_time.year, dz_time.month, dz_time.day).to_hijri()
        days_ar = ["الأحد", "الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت"]
        day_name = days_ar[dz_time.weekday() + 1 if dz_time.weekday() < 6 else 0]
        months_ar = ["محرم", "صفر", "ربيع الأول", "ربيع الثاني", "جمادى الأولى", "جمادى الآخرة", "رجب", "شعبان", "رمضان", "شوال", "ذو القعدة", "ذو الحجة"]
        return f"{day_name} {dz_time.day}/{dz_time.month}/{dz_time.year} م\n🌙 {h.day} {months_ar[h.month-1]} {h.year}هـ"
    except:
        return datetime.now().strftime("%d/%m/%Y") + " م"

def get_text():
    t = f"✨ <b>°° مُنظِّم الأدوار °°</b> ✨\n\n"
    t += f"🗓️ {get_hijri_date()}\n"
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
    # تأكدت من أن callback_data مطابقة تماماً لما في المعالج بالأسفل
    m.add(types.InlineKeyboardButton("📝 سجل اسمي", callback_data="reg"),
          types.InlineKeyboardButton("❌ حذف اسمي", callback_data="del"))
    m.add(types.InlineKeyboardButton("✅ قرأت", callback_data="done"),
          types.InlineKeyboardButton("🎧 مستمعة", callback_data="listn"))
    m.add(types.InlineKeyboardButton("🌸 إضافي", callback_data="extra_reg")) # تم تغيير الكلمة لضمان العمل
    m.add(types.InlineKeyboardButton("🔄 تحديث القائمة", callback_data="refresh_all"),
          types.InlineKeyboardButton("⚙️ الإعدادات", callback_data="admin_panel"))
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
def handle_callbacks(c):
    u_id = c.from_user.id
    u_name = c.from_user.first_name
    chat_id = c.message.chat.id
    
    # 1. معالجة زر الإضافي (تم فصله وتأكيده)
    if c.data == "extra_reg":
        if not any(p['id'] == u_id for p in data['readers']):
            data['readers'].append({'id': u_id, 'name': u_name, 'done': False, 'extra': True})
            bot.answer_callback_query(c.id, "تم تسجيلكِ كإضافي ✨")
        else:
            bot.answer_callback_query(c.id, "اسمكِ موجود بالفعل!")

    # 2. معالجة زر التحديث الشامل (إعادة إرسال)
    elif c.data == "refresh_all":
        try: bot.delete_message(chat_id, c.message.message_id)
        except: pass
        bot.send_message(chat_id, get_text(), parse_mode="HTML", reply_markup=main_menu(), disable_web_page_preview=True)
        return

    # بقية الأزرار
    elif c.data == "reg":
        if not any(p['id'] == u_id for p in data['readers']):
            data['readers'].append({'id': u_id, 'name': u_name, 'done': False, 'extra': False})
    elif c.data == "listn":
        if not any(p['id'] == u_id for p in data['listeners']):
            data['listeners'].append({'id': u_id, 'name': u_name})
    elif c.data == "done":
        for p in data['readers']:
            if p['id'] == u_id: p['done'] = True
    elif c.data == "del":
        data['readers'] = [p for p in data['readers'] if p['id'] != u_id]
        data['listeners'] = [p for p in data['listeners'] if p['id'] != u_id]
    elif c.data == "reset_now":
        data['readers'], data['listeners'] = [], []
    elif c.data == "admin_panel":
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("↕️ ترتيب الأسماء", callback_data="sort_list"),
              types.InlineKeyboardButton("🧨 تصفير شامل", callback_data="reset_now"))
        m.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="refresh_all"))
        bot.edit_message_reply_markup(chat_id, c.message.message_id, reply_markup=m)
        return

    # تحديث النص والرسالة بعد كل ضغطة
    try:
        bot.edit_message_text(get_text(), chat_id, c.message.message_id, parse_mode="HTML", reply_markup=main_menu(), disable_web_page_preview=True)
    except:
        pass

bot.infinity_polling()
