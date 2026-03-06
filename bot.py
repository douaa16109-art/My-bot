import telebot
from telebot import types
from flask import Flask
from threading import Thread

# --- السيرفر لضمان العمل 24 ساعة ---
app = Flask('')
@app.route('/')
def home(): return "Bot is running!"

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

TOKEN = '8753124430:AAFrkVk2xu8FlIdZYhYKXziJxlHY_We3v7Q'
bot = telebot.TeleBot(TOKEN)

# ذاكرة البوت
data = {
    'readers': [], 
    'listeners': [], 
    'is_open': True,
    'current_surah': "لم تحدد بعد"
}

def is_user_admin(chat_id, user_id):
    try:
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ['administrator', 'creator']
    except:
        return False

def generate_markup(chat_id, user_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    # أزرار العضوات (تظهر للجميع)
    markup.add(types.InlineKeyboardButton("🔄 اختيار الحالة", callback_data="choose_status"))
    markup.add(
        types.InlineKeyboardButton("✅ أتممت القراءة", callback_data="set_done"),
        types.InlineKeyboardButton("🗑️ حذف اسمي فقط", callback_data="user_del_self")
    )
    
    # أزرار المشرفات (مخفية تماماً عن العضوات)
    if is_user_admin(chat_id, user_id):
        markup.add(types.InlineKeyboardButton("🔃 تحديث القائمة", callback_data="admin_refresh"),
                   types.InlineKeyboardButton("📖 تغيير السورة", callback_data="admin_set_surah"))
        lock_text = "🔓 فتح التسجيل" if not data['is_open'] else "🔒 إغلاق التسجيل"
        markup.add(types.InlineKeyboardButton(lock_text, callback_data="toggle_lock"),
                   types.InlineKeyboardButton("🧨 تصفير القائمة", callback_data="admin_reset"))
        
    return markup

def build_report_text():
    status = "✅ مفتوحة" if data['is_open'] else "❌ مغلقة"
    text = "❄ **بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ** ❄\n"
    text += "🌿 **مَجْلِسُ تِلَاوَةِ القُرْآنِ الكَرِيمِ** 🌿\n\n"
    text += "📖 **اعْلَمِي رَعَاكِ اللهُ؛** أنَّ حُضوركِ لهذا المجلسِ محضُ توفيقٍ واصطفاءٍ من ربّكِ..\n"
    text += "━━━━━━━━━━━━━\n"
    text += f"حالة القائمة الآن: {status}\n"
    text += "━━━━━━━━━━━━━\n\n"
    
    # --- التعديل هنا: السورة فوق القارئات مباشرة ---
    text += f"📍 **السُّورَةُ الحَالِيَّةُ:** {data['current_surah']}\n"
    text += "📖 **قائمة القارئات:**\n"
    # ----------------------------------------------

    if not data['readers']: text += "لا يوجد مسجلات بعد..\n"
    else:
        for i, p in enumerate(data['readers'], 1):
            icon = "✅" if p['done'] else "⏳"
            text += f"{i}- {p['name']} {icon}\n"
            
    text += "\n🎧 **المستمعات:**\n"
    if not data['listeners']: text += "لا يوجد..\n"
    else:
        for i, p in enumerate(data['listeners'], 1):
            text += f"{i}- {p['name']} 🌿\n"
            
    return text

@bot.message_handler(commands=['start'])
def start_bot(m):
    if not is_user_admin(m.chat.id, m.from_user.id): return 
    msg = bot.send_message(m.chat.id, "📝 أهلاً بكِ أيتها المشرفة.. ما هي السورة الحالية؟")
    bot.register_next_step_handler(msg, save_surah_and_send_list)

def save_surah_and_send_list(m):
    data['current_surah'] = m.text
    bot.send_message(m.chat.id, build_report_text(), reply_markup=generate_markup(m.chat.id, m.from_user.id))

@bot.callback_query_handler(func=lambda call: True)
def handle_buttons(call):
    uid, uname, cid = call.from_user.id, call.from_user.first_name, call.message.chat.id
    
    # منع العضوات من استخدام أزرار المشرفات
    admin_cmds = ["admin_set_surah", "admin_refresh", "admin_reset", "toggle_lock"]
    if call.data in admin_cmds and not is_user_admin(cid, uid):
        bot.answer_callback_query(call.id, "عذراً، هذا الزر للمشرفات فقط! ❌", show_alert=True)
        return

    if call.data == "admin_set_surah":
        msg = bot.send_message(cid, "📝 أرسلي اسم السورة الجديدة:")
        bot.register_next_step_handler(msg, save_surah_and_send_list)

    elif call.data == "choose_status":
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("📖 تسجيل كقارئة", callback_data="reg_read"),
              types.InlineKeyboardButton("🎧 تسجيل كمستمعة", callback_data="reg_listen"))
        bot.edit_message_text("اختاري حالتكِ في المجلس:", cid, call.message.message_id, reply_markup=m)

    elif call.data == "reg_read":
        if not any(p['id'] == uid for p in data['readers']):
            data['readers'].append({'id': uid, 'name': uname, 'done': False})
        
    elif call.data == "reg_listen":
        if not any(p['id'] == uid for p in data['listeners']):
            data['listeners'].append({'id': uid, 'name': uname})

    elif call.data == "set_done":
        for p in data['readers']:
            if p['id'] == uid: p['done'] = True
        bot.answer_callback_query(call.id, "تَقَبَّلَ اللَّهُ طَاعَتَكِ ✅\n\n«سُبْحَانَكَ اللَّهُمَّ وَبِحَمْدِكَ، أَشْهَدُ أَنْ لَا إِلَهَ إِلَّا أَنْتَ، أَسْتَغْفِرُكَ وَأَتُوبُ إِلَيْكَ».", show_alert=True)

    elif call.data == "user_del_self":
        # حذف الشخص الذي ضغط فقط
        data['readers'] = [p for p in data['readers'] if p['id'] != uid]
        data['listeners'] = [p for p in data['listeners'] if p['id'] != uid]
        bot.answer_callback_query(call.id, "تم حذف اسمكِ بنجاح.")

    elif call.data == "admin_reset":
        data['readers'], data['listeners'] = [], []
        bot.answer_callback_query(call.id, "تم تصفير القائمة.")

    elif call.data == "toggle_lock":
        data['is_open'] = not data['is_open']

    elif call.data == "admin_refresh":
        bot.delete_message(cid, call.message.message_id)
        bot.send_message(cid, build_report_text(), reply_markup=generate_markup(cid, uid))

    try:
        bot.edit_message_text(build_report_text(), cid, call.message.message_id, reply_markup=generate_markup(cid, uid))
    except: pass

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()
