import telebot
from telebot import types
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "Bot is Ready!"
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

def get_text():
    # تنسيق العبارة مع الاقتباس
    t = "❄️ <b>بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ</b> ❄️\n"
    t += "🌿 <b>مَجْلِسُ تِلَاوَةِ القُرْآنِ الكريم</b> 🌿\n\n"
    t += "<blockquote>📖 اعْلَمِي رَعَاكِ اللَّه؛ أَنَّ حُضُورَكِ لِهَذَا المَجْلِسِ مَحْضُ تَوْفِيقٍ وَاصْطِفَاءٍ مِنْ رَبِّكِ.. فَكَمْ مِنْ مَحْرُومٍ وَالقُرْآنُ بَيْنَ يَدَيْهِ، وَكَمْ مِنْ مُوَفَّقٍ يُسَاقُ الخَيْرُ إِلَيْهِ!</blockquote>\n"
    t += "━━━━━━━━━━━━━\n\n"
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
            bot.answer_callback_query(c.id, "تم تسجيلكِ في القائمة الأساسية")

    elif c.data == "add_extra":
        data['readers'].append({'id': u_id, 'name': u_name, 'done': False, 'type': 'extra'})
        bot.answer_callback_query(c.id, "تم إضافة دور إضافي لكِ ✨")

    # ميزة "أتممت القراءة" بالترتيب (أساسي ثم إضافي 1 ثم إضافي 2...)
    elif c.data == "done":
        found = False
        # نبحث أولاً في الأدوار الأساسية
        for p in data['readers']:
            if p['id'] == u_id and p['type'] == 'main' and not p['done']:
                p['done'] = True
                found = True
                bot.answer_callback_query(c.id, "تم إنهاء دوركِ الأساسي ✅")
                break
        # إذا لم نجد دور أساسي مفتوح، نبحث في الأدوار الإضافية بالترتيب
        if not found:
            for p in data['readers']:
                if p['id'] == u_id and p['type'] == 'extra' and not p['done']:
                    p['done'] = True
                    found = True
                    bot.answer_callback_query(c.id, "تم إنهاء دور إضافي ✅")
                    break
        if not found:
            bot.answer_callback_query(c.id, "لا توجد أدوار مفتوحة باسمكِ!")

    elif c.data == "listn":
        if not any(p['id'] == u_id for p in data['listeners']):
            data['readers'] = [p for p in data['readers'] if p['id'] != u_id]
            data['listeners'].append({'id': u_id, 'name': u_name})
            bot.answer_callback_query(c.id, "تم تسجيلكِ كمستمعة 🌿")

    elif c.data == "admin_panel":
        m = types.InlineKeyboardMarkup()
        txt = "🔴 غلق الإضافي" if data['extra_open'] else "🟢 فتح الإضافي"
        m.add(types.InlineKeyboardButton(txt, callback_data="toggle_extra"))
        m.add(types.InlineKeyboardButton("🧨 تصفير شامل", callback_data="reset_all"))
        m.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="back_to_main"))
        return bot.edit_message_reply_markup(chat_id, c.message.message_id, reply_markup=m)

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
                data['readers'].pop(i)
                break
    elif c.data == "reset_all":
        data['readers'], data['listeners'] = [], []
    
    try:
        bot.edit_message_text(get_text(), chat_id, c.message.message_id, parse_mode="HTML", reply_markup=main_menu())
    except: pass

bot.infinity_polling()
