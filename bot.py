import telebot
from telebot import types
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "Bot is Fixed and Online!"
def run(): app.run(host='0.0.0.0', port=8080)
Thread(target=run).start()

TOKEN = '8684986706:AAF6pkJQ8a4N3XeecnnJOXhsJpr8z7gv8bs'
bot = telebot.TeleBot(TOKEN)

data = {'readers': [], 'listeners': [], 'surah': "قيد التحديد...", 'waiting': False}

def get_text():
    # النص مع تصحيح كلمة "السورة"
    t = "❄️ <b>بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ</b> ❄️\n"
    t += "🌿 <b>مَجْلِسُ تِلَاوَةِ القُرْآنِ الكريم</b> 🌿\n\n"
    t += "<blockquote>📖 اعْلَمِي رَعَاكِ اللَّه؛ أَنَّ حُضُورَكِ لِهَذَا المَجْلِسِ مَحْضُ تَوْفِيقٍ وَاصْطِفَاءٍ مِنْ رَبِّكِ.. فَكَمْ مِنْ مَحْرُومٍ وَالقُرْآنُ بَيْنَ يَدَيْهِ، وَكَمْ مِنْ مُوَفَّقٍ يُسَاقُ الخَيْرُ إِلَيْهِ!</blockquote>\n"
    t += "━━━━━━━━━━━━━\n\n"
    t += f"📍 <b>السُّورَةُ الحَالِيَّةُ:</b> {data['surah']}\n"
    t += "━━━━━━━━━━━━━\n\n"
    
    t += "🌷 <b><u>قَائِمَةُ القَارِئَاتِ:</u></b>\n"
    readers = [p for p in data['readers'] if not p['extra']]
    if not readers: t += "لا يوجد مسجلات بعد..\n"
    else:
        for i, p in enumerate(readers, 1):
            s = "✅" if p['done'] else "⏳"
            t += f"{i}- <a href='tg://user?id={p['id']}'>{p['name']}</a> {s}\n"
            
    t += "\n🌿 <b><u>الأدوار الإضافية:</u></b>\n"
    extras = [p for p in data['readers'] if p['extra']]
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
    m.add(types.InlineKeyboardButton("🌸 إضافي", callback_data="extra_reg"))
    m.add(types.InlineKeyboardButton("🔄 تحديث (إرسال جديد)", callback_data="refresh_bot"))
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
    
    # خيار الحذف (أساسي أو إضافي)
    if c.data == "ask_del":
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("❌ حذف من الأساسي", callback_data="del_main"),
              types.InlineKeyboardButton("❌ حذف من الإضافي", callback_data="del_extra"))
        m.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="back"))
        return bot.edit_message_reply_markup(chat_id, c.message.message_id, reply_markup=m)

    elif c.data == "del_main":
        data['readers'] = [p for p in data['readers'] if not (p['id'] == u_id and not p['extra'])]
        bot.answer_callback_query(c.id, "تم الحذف من القائمة الأساسية")
    elif c.data == "del_extra":
        data['readers'] = [p for p in data['readers'] if not (p['id'] == u_id and p['extra'])]
        bot.answer_callback_query(c.id, "تم الحذف من الإضافي")

    # زر التحديث (إعادة إرسال وحذف القديم)
    elif c.data == "refresh_bot":
        try: bot.delete_message(chat_id, c.message.message_id)
        except: pass
        return bot.send_message(chat_id, get_text(), parse_mode="HTML", reply_markup=main_menu())

    elif c.data == "reg":
        if not any(p['id']==u_id and not p['extra'] for p in data['readers']):
            data['readers'].append({'id':u_id, 'name':u_name, 'done':False, 'extra':False})
    elif c.data == "extra_reg":
        if not any(p['id']==u_id and p['extra'] for p in data['readers']):
            data['readers'].append({'id':u_id, 'name':u_name, 'done':False, 'extra':True})
    elif c.data == "listn":
        if not any(p['id']==u_id for p in data['listeners']):
            data['listeners'].append({'id':u_id, 'name':u_name})
    elif c.data == "done":
        for p in data['readers']:
            if p['id'] == u_id: p['done'] = True
    elif c.data == "back":
        pass 

    try:
        bot.edit_message_text(get_text(), chat_id, c.message.message_id, parse_mode="HTML", reply_markup=main_menu())
    except: pass

bot.infinity_polling()
