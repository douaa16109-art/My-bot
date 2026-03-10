import telebot
from telebot import types
from datetime import datetime, timedelta
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "Bot is Ready for Manual Sorting!"
def run(): app.run(host='0.0.0.0', port=8080)
Thread(target=run).start()

TOKEN = '8684986706:AAF6pkJQ8a4N3XeecnnJOXhsJpr8z7gv8bs'
bot = telebot.TeleBot(TOKEN)

data = {
    'readers': [], 
    'listeners': [], 
    'surah': "قيد التحديد...", 
    'waiting': False,
    'extra_open': False 
}

def get_hijri_date():
    today = datetime.utcnow() + timedelta(hours=3)
    days_ar = ["الأحد", "الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت"]
    day_name = days_ar[(today.weekday() + 1) % 7]
    hijri_day = today.day + 10 
    if hijri_day > 30: hijri_day -= 30
    m_date = today.strftime("%d مارس 2026")
    return f"📅 {day_name} {m_date} م\n🌙 {hijri_day} رمضان 1447 هـ"

def get_text():
    t = "❄️ <b>بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ</b> ❄️\n"
    t += "🌿 <b>مَجْلِسُ تِلَاوَةِ القُرْآنِ الكريم</b> 🌿\n\n"
    t += f"{get_hijri_date()}\n"
    t += " 🔅┈┈┈•●◈💠◈●•┈┈┈🔅\n\n"
    t += "<blockquote>📖 اعْلَمِي رَعَاكِ اللَّه؛ أَنَّ حُضُورَكِ لِهَذَا المَجْلِسِ مَحْضُ تَوْفِيقٍ وَاصْطِفَاءٍ مِنْ رَبِّكِ.. فَكَمْ مِنْ مَحْرُومٍ وَالقُرْآنُ بَيْنَ يَدَيْهِ، وَكَمْ مِنْ مُوَفَّقٍ يُسَاقُ الخَيْرُ إِلَيْهِ!</blockquote>\n"
    t += " 🔅┈┈┈•●◈💠◈●•┈┈┈🔅\n\n"
    t += f"📍 <b>السُّورَةُ الحَالِيَّةُ:</b> {data['surah']}\n"
    t += "━━━━━━━━━━━━━\n\n"
    
    t += "🌷 <b><u>قَائِمَةُ القَارِئَاتِ:</u></b>\n"
    readers = [p for p in data['readers'] if p['type'] == 'main']
    if not readers: t += "لا يوجد مسجلات بعد..\n"
    else:
        for i, p in enumerate(readers, 1):
            s = "✅" if p['done'] else "⏳"
            t += f"{i}- <a href='tg://user?id={p['id']}'>{p['name']}</a> {s}\n"
            
    t += "\n🌿 <b><u>الأدوار الإضافية:</u></b>\n"
    extras = [p for p in data['readers'] if p['type'] == 'extra']
    if not extras: t += "لا يوجد مسجلات بعد..\n"
    else:
        for i, p in enumerate(extras, 1):
            s = "✅" if p['done'] else "⏳"
            t += f"{i}- <a href='tg://user?id={p['id']}'>{p['name']}</a> {s}\n"

    t += "\n🌷 <b><u>المُسْتَمِعَاتُ:</u></b>\n"
    if not data['listeners']: t += "لا يوجد..\n"
    else:
        for i, p in enumerate(data['listeners'], 1):
            t += f"{i}- <a href='tg://user?id={p['id']}'>{p['name']}</a> 🌿\n"
    
    t += "\n 🔅┈┈┈•●◈💠◈●•┈┈┈🔅\n"
    t += "اللهم اجعلنا ممن يقال لهم:\n<b>(اقرأ وارتقِ ورتل كما كنت ترتل في الدنيا)</b>"
    return t

def main_menu():
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
    data['waiting'] = True
    bot.send_message(m.chat.id, "📝 حياكِ الله يا مشرفة.. اكتبي اسم السورة الآن:")

@bot.message_handler(func=lambda m: data['waiting'])
def set_surah(m):
    data['surah'] = m.text
    data['waiting'] = False
    bot.send_message(m.chat.id, get_text(), parse_mode="HTML", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda c: True)
def handle_calls(c):
    u_id, u_name, chat_id = c.from_user.id, c.from_user.first_name, c.message.chat.id
    
    if c.data == "refresh_bot":
        try: bot.delete_message(chat_id, c.message.message_id)
        except: pass
        return bot.send_message(chat_id, get_text(), parse_mode="HTML", reply_markup=main_menu())

    elif c.data == "reg":
        if not any(p['id'] == u_id and p['type'] == 'main' for p in data['readers']):
            data['readers'].append({'id': u_id, 'name': u_name, 'done': False, 'type': 'main'})
    
    elif c.data == "add_extra":
        data['readers'].append({'id': u_id, 'name': u_name, 'done': False, 'type': 'extra'})

    elif c.data == "done":
        for p in data['readers']:
            if p['id'] == u_id and not p['done']:
                p['done'] = True
                bot.answer_callback_query(c.id, "✅")
                break

    elif c.data == "admin_panel":
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("🟢 فتح/غلق الإضافي", callback_data="toggle_extra"))
        m.add(types.InlineKeyboardButton("↕️ تقديم/تأخير الأسماء", callback_data="manual_sort"))
        m.add(types.InlineKeyboardButton("🧨 تصفير شامل", callback_data="reset_all"))
        m.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="back_to_main"))
        return bot.edit_message_reply_markup(chat_id, c.message.message_id, reply_markup=m)

    # نظام الترتيب اليدوي (Manual Sort)
    elif c.data == "manual_sort":
        m = types.InlineKeyboardMarkup()
        for i, p in enumerate(data['readers']):
            t_label = "(إضافي)" if p['type'] == 'extra' else "(أساسي)"
            m.add(types.InlineKeyboardButton(f"{p['name']} {t_label}", callback_data=f"sel_{i}"))
        m.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="admin_panel"))
        return bot.edit_message_reply_markup(chat_id, c.message.message_id, reply_markup=m)

    elif c.data.startswith("sel_"):
        idx = int(c.data.split("_")[1])
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("⬆️ تقديم (فوق)", callback_data=f"up_{idx}"),
              types.InlineKeyboardButton("⬇️ تأخير (تحت)", callback_data=f"down_{idx}"))
        m.add(types.InlineKeyboardButton("⬅️ رجوع للأسماء", callback_data="manual_sort"))
        return bot.edit_message_reply_markup(chat_id, c.message.message_id, reply_markup=m)

    elif c.data.startswith("up_"):
        idx = int(c.data.split("_")[1])
        if idx > 0:
            data['readers'][idx], data['readers'][idx-1] = data['readers'][idx-1], data['readers'][idx]
        return handle_calls(types.CallbackQuery(c.id, c.from_user, c.message, c.chat_instance, "manual_sort"))

    elif c.data.startswith("down_"):
        idx = int(c.data.split("_")[1])
        if idx < len(data['readers']) - 1:
            data['readers'][idx], data['readers'][idx+1] = data['readers'][idx+1], data['readers'][idx]
        return handle_calls(types.CallbackQuery(c.id, c.from_user, c.message, c.chat_instance, "manual_sort"))

    elif c.data == "toggle_extra":
        data['extra_open'] = not data['extra_open']
        return handle_calls(types.CallbackQuery(c.id, c.from_user, c.message, c.chat_instance, "admin_panel"))

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
    elif c.data == "reset_all":
        data['readers'], data['listeners'] = [], []
    
    try:
        bot.edit_message_text(get_text(), chat_id, c.message.message_id, parse_mode="HTML", reply_markup=main_menu())
    except: pass

bot.infinity_polling()
