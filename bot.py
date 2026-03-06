import telebot
from telebot import types
from flask import Flask
from threading import Thread

# --- إعداد السيرفر لضمان العمل 24 ساعة ---
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
    'is_open': True
}

def is_user_admin(chat_id, user_id):
    if chat_id > 0: return True 
    try:
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ['administrator', 'creator']
    except: return False

def generate_main_markup(chat_id, user_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("🔄 اختيار الحالة (قارئة/مستمعة)", callback_data="choose_status"))
    
    markup.add(
        types.InlineKeyboardButton("✅ أتممت القراءة", callback_data="set_done"),
        types.InlineKeyboardButton("🗑️ حذف اسمي", callback_data="user_del")
    )
    
    if is_user_admin(chat_id, user_id):
        markup.add(types.InlineKeyboardButton("🔃 تحديث القائمة", callback_data="admin_refresh"))
        lock_text = "🔓 فتح التسجيل" if not data['is_open'] else "🔒 إغلاق التسجيل"
        markup.add(types.InlineKeyboardButton(lock_text, callback_data="toggle_lock"),
                   types.InlineKeyboardButton("🧨 تصفير القائمة", callback_data="admin_reset"))
        markup.add(types.InlineKeyboardButton("⚙️ لوحة الحذف", callback_data="admin_del_panel"))
        
    return markup

def build_report_text():
    status = "✅ مفتوحة" if data['is_open'] else "❌ مغلقة"
    
    # النص المختصر والمعدل كما طلبتِ
    text = "❄ **بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ** ❄\n"
    text += "🌿 **مَجْلِسُ تِلَاوَةِ القُرْآنِ الكَرِيمِ** 🌿\n\n"
    text += "📖 **اعْلَمِي رَعَاكِ اللهُ؛** أنَّ حُضوركِ لهذا المجلسِ ليس بجهدكِ ولا باختياركِ، بل هو محضُ توفيقٍ واصطفاءٍ من ربّكِ.. فكم من محرومٍ والقرآنُ بين يديه، وكم من مُوفّقٍ يُساقُ الخيرُ إليه!\n\n"
    text += "━━━━━━━━━━━━━\n"
    text += f"حالة القائمة الآن: {status}\n"
    text += "━━━━━━━━━━━━━\n\n"
    
    text += "📖 **قائمة القارئات:**\n"
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
    bot.send_message(m.chat.id, build_report_text(), reply_markup=generate_main_markup(m.chat.id, m.from_user.id))

@bot.callback_query_handler(func=lambda call: True)
def handle_buttons(call):
    uid, uname, cid = call.from_user.id, call.from_user.first_name, call.message.chat.id
    
    if call.data == "choose_status":
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("📖 تسجيل كقارئة", callback_data="reg_read"),
              types.InlineKeyboardButton("🎧 تسجيل كمستمعة", callback_data="reg_listen"))
        m.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="back"))
        bot.edit_message_text("اختاري حالتكِ في المجلس:", cid, call.message.message_id, reply_markup=m)
        return

    elif call.data == "reg_read":
        if not any(p['id'] == uid for p in data['readers']):
            data['readers'].append({'id': uid, 'name': uname, 'done': False})
        
    elif call.data == "reg_listen":
        if not any(p['id'] == uid for p in data['listeners']):
            data['listeners'].append({'id': uid, 'name': uname})

    elif call.data == "set_done":
        found = False
        for p in data['readers']:
            if p['id'] == uid:
                p['done'] = True
                found = True
        
        if found:
            # التنبيه العلوي مع الأذكار المضبوطة بالشكل
            alert_text = "تَقَبَّلَ اللَّهُ طَاعَتَكِ ✅\n\n"
            alert_text += "لا تنسي قول: «سُبْحَانَكَ اللَّهُمَّ وَبِحَمْدِكَ، أَشْهَدُ أَنْ لَا إِلَهَ إِلَّا أَنْتَ، أَسْتَغْفِرُكَ وَأَتُوبُ إِلَيْكَ».\n\n"
            alert_text += "اللَّهُمَّ اجْعَلْنَا مِنْ أَهْلِ القُرْآنِ الَّذِينَ هُمْ أَهْلُكَ وَخَاصَّتُكَ."
            bot.answer_callback_query(call.id, alert_text, show_alert=True)
        else:
            bot.answer_callback_query(call.id, "يجب التسجيل أولاً!")

    elif call.data == "admin_refresh":
        bot.delete_message(cid, call.message.message_id)
        bot.send_message(cid, build_report_text(), reply_markup=generate_main_markup(cid, uid))
        return

    elif call.data == "admin_reset":
        if is_user_admin(cid, uid):
            data['readers'], data['listeners'] = [], []
            bot.answer_callback_query(call.id, "تم تصفير القائمة.")

    elif call.data == "user_del":
        data['readers'] = [p for p in data['readers'] if p['id'] != uid]
        data['listeners'] = [p for p in data['listeners'] if p['id'] != uid]

    elif call.data == "toggle_lock":
        if is_user_admin(cid, uid): data['is_open'] = not data['is_open']

    elif call.data == "admin_del_panel":
        if is_user_admin(cid, uid):
            del_m = types.InlineKeyboardMarkup()
            for p in data['readers']:
                del_m.add(types.InlineKeyboardButton(f"🗑️ {p['name']}", callback_data=f"del_{p['id']}"))
            del_m.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="back"))
            bot.edit_message_text("لوحة الحذف:", cid, call.message.message_id, reply_markup=del_m)
            return

    elif call.data.startswith("del_"):
        target_id = int(call.data.split("_")[1])
        data['readers'] = [p for p in data['readers'] if p['id'] != target_id]

    try:
        bot.edit_message_text(build_report_text(), cid, call.message.message_id, reply_markup=generate_main_markup(cid, uid))
    except: pass

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()
