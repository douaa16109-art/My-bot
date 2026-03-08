import telebot
from telebot import types
from flask import Flask
from threading import Thread
import time

# --- السيرفر لضمان العمل 24 ساعة ---
app = Flask('')
@app.route('/')
def home(): return "Bot is running!"

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

# التوكن الجديد الخاص بكِ
TOKEN = '8753124430:AAHjTw4-KRaNUSE5OznIwMjzFaXN6ll2FIM'
bot = telebot.TeleBot(TOKEN)

data = {'readers': [], 'listeners': [], 'is_open': True, 'current_surah': "لم تحدد بعد"}

def get_user_rank(chat_id, user_id):
    try:
        if chat_id > 0: return True 
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ['administrator', 'creator']
    except: return False

def generate_markup(chat_id, user_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    is_admin = get_user_rank(chat_id, user_id)
    markup.add(types.InlineKeyboardButton("🔄 اختيار الحالة", callback_data="choose_status"))
    markup.add(types.InlineKeyboardButton("✅ أتممت القراءة", callback_data="set_done"),
               types.InlineKeyboardButton("🗑️ حذف اسمي فقط", callback_data="user_del_self"))
    if is_admin:
        markup.add(types.InlineKeyboardButton("🔃 تحديث القائمة", callback_data="admin_refresh"),
                   types.InlineKeyboardButton("📖 تغيير السورة", callback_data="admin_set_surah"))
        lock_text = "🔓 فتح التسجيل" if not data['is_open'] else "🔒 إغلاق التسجيل"
        markup.add(types.InlineKeyboardButton(lock_text, callback_data="toggle_lock"),
                   types.InlineKeyboardButton("🧨 تصفير القائمة", callback_data="admin_reset"))
        markup.add(types.InlineKeyboardButton("⚙️ إدارة الأسماء والترتيب", callback_data="admin_manage_panel"))
    return markup

def build_report_text():
    status = "✅ مفتوحة" if data['is_open'] else "❌ مغلقة"
    text = "❄️ *بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ* ❄️\n🌿 *مَجْلِسُ تِلَاوَةِ القُرْآنِ الكَرِيمِ* 🌿\n\n"
    text += ">📖 **اعْلَمِي رَعَاكِ اللهُ؛ أنَّ حُضوركِ لهذا المجلسِ محضُ توفيقٍ واصطفاءٍ من ربّكِ\\.\\.**\n\n"
    text += f"━━━━━━━━━━━━━\nحالة القائمة الآن: {status}\n━━━━━━━━━━━━━\n\n"
    text += f"📍 *السُّورَةُ الحَالِيَّةُ: {data['current_surah']}*\n━━━━━━━━━━━━━\n\n🌷 *قَائِمَةُ القَارِئَاتِ* 🌷\n"
    if not data['readers']: text += "لا يوجد مسجلات بعد\\.\\.\n"
    else:
        for i, p in enumerate(data['readers'], 1):
            icon = "✅" if p['done'] else "⏳"
            text += f"{i}\\- {p['name']} {icon}\n"
    text += "\n━━━━━━━━━━━━━\n🌷 *المُسْتَمِعَاتُ* 🌷\n"
    if not data['listeners']: text += "لا يوجد\\.\\.\n"
    else:
        for i, p in enumerate(data['listeners'], 1): text += f"{i}\\- {p['name']} 🌿\n"
    return text

@bot.message_handler(commands=['start'])
def start_bot(m):
    if not get_user_rank(m.chat.id, m.from_user.id): return 
    msg = bot.send_message(m.chat.id, "📝 ما هي السورة الحالية؟")
    bot.register_next_step_handler(msg, save_surah_and_send_list)

def save_surah_and_send_list(m):
    data['current_surah'] = m.text
    bot.send_message(m.chat.id, build_report_text(), parse_mode="MarkdownV2", reply_markup=generate_markup(m.chat.id, m.from_user.id))

@bot.callback_query_handler(func=lambda call: True)
def handle_buttons(call):
    uid, uname, cid = call.from_user.id, call.from_user.first_name, call.message.chat.id
    is_admin = get_user_rank(cid, uid)
    if "admin_" in call.data and not is_admin: return
    
    if call.data == "choose_status" and data['is_open']:
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("📖 تسجيل كقارئة", callback_data="reg_read"),
              types.InlineKeyboardButton("🎧 تسجيل كمستمعة", callback_data="reg_listen"))
        bot.edit_message_text("اختاري حالتكِ:", cid, call.message.message_id, reply_markup=m)
        return
    
    if call.data == "reg_read":
        data['listeners'] = [p for p in data['listeners'] if p['id'] != uid]
        if not any(p['id'] == uid for p in data['readers']): data['readers'].append({'id': uid, 'name': uname, 'done': False})
    elif call.data == "reg_listen":
        data['readers'] = [p for p in data['readers'] if p['id'] != uid]
        if not any(p['id'] == uid for p in data['listeners']): data['listeners'].append({'id': uid, 'name': uname})
    elif call.data == "set_done":
        for p in data['readers']:
            if p['id'] == uid: p['done'] = True
    elif call.data == "user_del_self":
        data['readers'] = [p for p in data['readers'] if p['id'] != uid]
        data['listeners'] = [p for p in data['listeners'] if p['id'] != uid]
    elif is_admin and call.data == "admin_manage_panel":
        m = types.InlineKeyboardMarkup()
        for p in data['readers'] + data['listeners']:
            m.add(types.InlineKeyboardButton(f"👤 {p['name']}", callback_data=f"opts_{p['id']}"))
        m.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="back_to_main"))
        bot.edit_message_text("⚙️ إدارة الأسماء:", cid, call.message.message_id, reply_markup=m)
        return

    bot.edit_message_text(build_report_text(), cid, call.message.message_id, parse_mode="MarkdownV2", reply_markup=generate_markup(cid, uid))

if __name__ == "__main__":
    keep_alive()
    # سطر الطوارئ: حذف الـ Webhook القديم وإيقاف أي جلسة سابقة
    bot.remove_webhook()
    time.sleep(2) 
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
