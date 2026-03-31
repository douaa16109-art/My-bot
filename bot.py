import telebot
from telebot import types
from datetime import datetime, timedelta
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "Date Fixed - 20 Ramadan!"
def run(): app.run(host='0.0.0.0', port=8080)
Thread(target=run).start()

TOKEN = '8684986706:AAF6pkJQ8a4N3XeecnnJOXhsJpr8z7gv8bs'
bot = telebot.TeleBot(TOKEN)

groups_data = {}

def get_group_data(chat_id):
    if chat_id not in groups_data:
        groups_data[chat_id] = {
            'readers': [], 'listeners': [], 'surah': "قيد التحديد...", 
            'waiting': False, 'extra_open': False 
        }
    return groups_data[chat_id]

def get_hijri_date():
    # توقيت مكة المكرمة
    now = datetime.utcnow() + timedelta(hours=3)
    days_ar = ["الأحد", "الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت"]
    day_name = days_ar[(now.weekday() + 1) % 7]
    
    # تثبيت الحساب يدوياً لضمان عدم القفز لشوال
    # اليوم 1 أبريل يقابل 20 رمضان بناءً على طلبك السابق
    base_date = datetime(2026, 4, 1) 
    delta_days = (now.date() - base_date.date()).days
    hijri_day = 20 + delta_days 
    
    m_date = now.strftime("%d %B 2026").replace("April", "أبريل").replace("March", "مارس")
    return f"📅 {day_name} {m_date} م\n🌙 {hijri_day} رمضان 1447 هـ"

def get_text(chat_id):
    data = get_group_data(chat_id)
    t = "❄️ <b>بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ</b> ❄️\n"
    t += "🌿 <b>مَجْلِسُ تِلَاوَةِ القُرْآنِ الكريم</b> 🌿\n\n"
    t += f"{get_hijri_date()}\n"
    t += "☀️ ┈┈┈•●◈💠◈●•┈┈┈ ☀️\n\n"
    t += "<blockquote>📖 اعْلَمِي رَعَاكِ اللَّه؛ أَنَّ حُضُورَكِ لِهَذَا المَجْلِسِ مَحْضُ تَوْفِيقٍ وَاصْطِفَاءٍ مِنْ رَبِّكِ.. فَكَمْ مِنْ مَحْرُومٍ وَالقُرْآنُ بَيْنَ يَدَيْهِ، وَكَمْ مِنْ مُوَفَّقٍ يُسَاقُ الخَيْرُ إِلَيْهِ!</blockquote>\n"
    t += "☀️ ┈┈┈•●◈💠◈●•┈┈┈ ☀️\n\n"
    t += f"📍 <b>السُّورَةُ الحَالِيَّةُ:</b> {data['surah']}\n"
    t += "━━━━━━━━━━━━━\n\n"
    t += "🌷 <b><u>قَائِمَةُ القَارِئَاتِ:</u></b>\n"
    if not data['readers']: t += "لا يوجد مسجلات بعد..\n"
    else:
        for i, p in enumerate(data['readers'], 1):
            s = "✅" if p['done'] else "⌛"
            tag = " (إضافي)" if p['type'] == 'extra' else ""
            t += f"{i}- <a href='tg://user?id={p['id']}'>{p['name']}</a>{tag} {s}\n"
    t += "\n🌷 <b><u>المُسْتَمِعَاتُ:</u></b>\n"
    if not data['listeners']: t += "لا يوجد..\n"
    else:
        for i, p in enumerate(data['listeners'], 1):
            t += f"{i}- <a href='tg://user?id={p['id']}'>{p['name']}</a> 🌿\n"
    t += "\n☀️ ┈┈┈•●◈💠◈●•┈┈┈ ☀️\n"
    t += "اللهم اجعلنا ممن يقال لهم:\n<b>(اقرأ وارتقِ ورتل كما كنت ترتل في الدنيا)</b>"
    return t

def main_menu(chat_id):
    data = get_group_data(chat_id)
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(types.InlineKeyboardButton("📝 سجل اسمي", callback_data="reg"),
          types.InlineKeyboardButton("❌ حذف اسمي", callback_data="ask_del"))
    m.add(types.InlineKeyboardButton("✅ أتممت القراءة", callback_data="done"),
          types.InlineKeyboardButton("🎧 مستمعة", callback_data="listn"))
    if data['extra_open']:
        m.add(types.InlineKeyboardButton("🌸 اخذ دور اضافي", callback_data="add_extra"))
    m.add(types.InlineKeyboardButton("🔄 تحديث", callback_data="refresh_bot"),
          types.InlineKeyboardButton("⚙️ الإعدادات", callback_data="admin_panel"))
    return m

@bot.message_handler(commands=['start'])
def start(m):
    status = bot.get_chat_member(m.chat.id, m.from_user.id).status
    if status not in ['administrator', 'creator']:
        return bot.answer_callback_query(m.chat.id, "⚠️ للمشرفات فقط")
    data = get_group_data(m.chat.id)
    data['waiting'] = True
    bot.send_message(m.chat.id, "📝 حياكِ الله يا مشرفة.. اكتبي اسم السورة الآن:")

@bot.message_handler(func=lambda m: get_group_data(m.chat.id).get('waiting', False))
def set_surah(m):
    data = get_group_data(m.chat.id)
    data['surah'], data['waiting'] = m.text, False
    bot.send_message(m.chat.id, get_text(m.chat.id), parse_mode="HTML", reply_markup=main_menu(m.chat.id))

@bot.callback_query_handler(func=lambda c: True)
def handle_calls(c):
    chat_id = c.message.chat.id
    data = get_group_data(chat_id)
    u_id, u_name = c.from_user.id, c.from_user.first_name
    
    if c.data in ["admin_panel", "manual_sort", "reset_all", "toggle_extra", "refresh_bot"]:
        status = bot.get_chat_member(chat_id, u_id).status
        if status not in ['administrator', 'creator']:
            return bot.answer_callback_query(c.id, "⚠️ عذراً، هذا الخيار للمشرفات فقط.", show_alert=True)

    bot.answer_callback_query(c.id)

    if c.data == "refresh_bot":
        try: bot.delete_message(chat_id, c.message.message_id)
        except: pass
        return bot.send_message(chat_id, get_text(chat_id), parse_mode="HTML", reply_markup=main_menu(chat_id))

    elif c.data == "reg":
        if not any(p['id'] == u_id and p['type'] == 'main' for p in data['readers']):
            data['readers'].append({'id': u_id, 'name': u_name, 'done': False, 'type': 'main'})
    
    elif c.data == "add_extra":
        data['readers'].append({'id': u_id, 'name': u_name, 'done': False, 'type': 'extra'})

    elif c.data == "listn":
        if not any(p['id'] == u_id for p in data['listeners']):
            data['listeners'].append({'id': u_id, 'name': u_name})

    elif c.data == "done":
        for p in data['readers']:
            if p['id'] == u_id and not p['done']:
                p['done'] = True
                break

    elif c.data == "admin_panel":
        m = types.InlineKeyboardMarkup()
        txt = "🔴 غلق الإضافي" if data['extra_open'] else "🟢 فتح الإضافي"
        m.add(types.InlineKeyboardButton(txt, callback_data="toggle_extra"))
        m.add(types.InlineKeyboardButton("↕️ تقديم وتأخير الأسماء", callback_data="manual_sort"))
        m.add(types.InlineKeyboardButton("🧨 تصفير شامل", callback_data="reset_all"))
        m.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="back_to_main"))
        return bot.edit_message_reply_markup(chat_id, c.message.message_id, reply_markup=m)

    elif c.data == "manual_sort":
        m = types.InlineKeyboardMarkup()
        for i, p in enumerate(data['readers']):
            tag = " (إضافي)" if p['type'] == 'extra' else ""
            m.add(types.InlineKeyboardButton(f"{i+1}- {p['name']}{tag}", callback_data=f"sel_{i}"))
        m.add(types.InlineKeyboardButton("⬅️ رجوع للوحة", callback_data="admin_panel"))
        return bot.edit_message_reply_markup(chat_id, c.message.message_id, reply_markup=m)

    elif c.data.startswith("sel_"):
        idx = int(c.data.split("_")[1])
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("⬆️ تقديم", callback_data=f"up_{idx}"),
              types.InlineKeyboardButton("⬇️ تأخير", callback_data=f"down_{idx}"))
        m.add(types.InlineKeyboardButton("⬅️ رجوع للأسماء", callback_data="manual_sort"))
        return bot.edit_message_reply_markup(chat_id, c.message.message_id, reply_markup=m)

    elif c.data.startswith(("up_", "down_")):
        cmd, idx = c.data.split("_")
        idx = int(idx)
        if cmd == "up" and idx > 0:
            data['readers'][idx], data['readers'][idx-1] = data['readers'][idx-1], data['readers'][idx]
        elif cmd == "down" and idx < len(data['readers']) - 1:
            data['readers'][idx], data['readers'][idx+1] = data['readers'][idx+1], data['readers'][idx]
        
        m = types.InlineKeyboardMarkup()
        for i, p in enumerate(data['readers']):
            tag = " (إضافي)" if p['type'] == 'extra' else ""
            m.add(types.InlineKeyboardButton(f"{i+1}- {p['name']}{tag}", callback_data=f"sel_{i}"))
        m.add(types.InlineKeyboardButton("⬅️ رجوع للوحة", callback_data="admin_panel"))
        bot.edit_message_reply_markup(chat_id, c.message.message_id, reply_markup=m)
        try: bot.edit_message_text(get_text(chat_id), chat_id, c.message.message_id, parse_mode="HTML", reply_markup=m)
        except: pass
        return

    elif c.data == "toggle_extra":
        data['extra_open'] = not data['extra_open']
    
    elif c.data == "reset_all":
        data['readers'], data['listeners'] = [], []

    elif c.data == "ask_del":
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("❌ حذف الأساسي", callback_data="del_main"),
              types.InlineKeyboardButton("❌ حذف الإضافي", callback_data="del_extra"))
        m.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="back_to_main"))
        return bot.edit_message_reply_markup(chat_id, c.message.message_id, reply_markup=m)

    elif c.data == "del_main":
        data['readers'] = [p for p in data['readers'] if not (p['id'] == u_id and p['type'] == 'main')]
    elif c.data == "del_extra":
        for i in range(len(data['readers'])-1, -1, -1):
            if data['readers'][i]['id'] == u_id and data['readers'][i]['type'] == 'extra':
                data['readers'].pop(i); break
    
    try:
        bot.edit_message_text(get_text(chat_id), chat_id, c.message.message_id, parse_mode="HTML", reply_markup=main_menu(chat_id))
    except: pass

bot.infinity_polling()
