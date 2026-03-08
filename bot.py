import telebot
from telebot import types
from flask import Flask
from threading import Thread
import time

app = Flask('')
@app.route('/')
def home(): return "Bot is running!"

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

# التوكن الخاص بكِ
TOKEN = '8753124430:AAHjTw4-KRaNUSE5OznIwMjzFaXN6ll2FIM'
bot = telebot.TeleBot(TOKEN)

# الذاكرة
data = {'readers': [], 'listeners': [], 'extra_roles': [], 'is_open': True, 'extra_locked': False, 'current_surah': "لم تحدد بعد"}

def get_user_rank(chat_id, user_id):
    try:
        if chat_id > 0: return True 
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ['administrator', 'creator']
    except: return False

def generate_markup(chat_id, user_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    is_admin = get_user_rank(chat_id, user_id)
    markup.add(types.InlineKeyboardButton("🔄 اختيار الحالة (قارئة/مستمعة)", callback_data="choose_status"))
    markup.add(types.InlineKeyboardButton("🗑️ حذف اسمي فقط", callback_data="user_del_self"),
               types.InlineKeyboardButton("✅ أتممت القراءة", callback_data="set_done"))
    # زر الإضافي المستقل كما في الصورة القديمة
    extra_btn_text = "🌿 تفعيل الإضافي" if not data['extra_locked'] else "🌿 الإضافي (مغلق)"
    markup.add(types.InlineKeyboardButton(extra_btn_text, callback_data="reg_extra"))
    if is_admin:
        markup.add(types.InlineKeyboardButton("🔄 تحديث القائمة", callback_data="admin_refresh"),
                   types.InlineKeyboardButton("📖 تغيير السورة", callback_data="admin_set_surah"))
        lock_text = "🔒 إغلاق التسجيل" if data['is_open'] else "🔓 فتح التسجيل"
        extra_lock_text = "🔒 قفل الإضافي" if not data['extra_locked'] else "🔓 فتح الإضافي"
        markup.add(types.InlineKeyboardButton(lock_text, callback_data="toggle_lock"),
                   types.InlineKeyboardButton(extra_lock_text, callback_data="toggle_extra_lock"))
        markup.add(types.InlineKeyboardButton("🧨 تصفير", callback_data="admin_reset"),
                   types.InlineKeyboardButton("⚙️ إدارة الأسماء والترتيب", callback_data="admin_manage_panel"))
    return markup

def build_report_text():
    status = "✅ مفتوحة" if data['is_open'] else "❌ مغلقة"
    text = "❄️ *بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ* ❄️\n🌿 *مَجْلِسُ تِلَاوَةِ القُرْآنِ الكَرِيمِ* 🌿\n\n"
    text += ">📖 **اعْلَمِي رَعَاكِ اللهُ؛ أنَّ حُضوركِ لهذا المجلسِ محضُ توفيقٍ واصطفاءٍ من ربّكِ\\.\\. فكم من محرومٍ والقرآنُ بين يديه، وكم من مُوفّقٍ يُساقُ الخيرُ إليه\\!**\n\n"
    text += f"━━━━━━━━━━━━━\nحالة القائمة الآن: {status}\n━━━━━━━━━━━━━\n\n"
    text += f"📍 *السُّورَةُ الحَالِيَّةُ: {data['current_surah']}*\n━━━━━━━━━━━━━\n\n"
    text += "🌷 *قَائِمَةُ القَارِئَاتِ* 🌷\n"
    if not data['readers']: text += "لا يوجد مسجلات بعد\\.\\.\n"
    else:
        for i, p in enumerate(data['readers'], 1): text += f"{i}\\- {p['name']} {'✅' if p['done'] else '⏳'}\n"
    text += "\n🌿 *الأدوار الإضافية* 🌿\n"
    if not data['extra_roles']: text += "لا يوجد مسجلات بعد\\.\\.\n"
    else:
        for i, p in enumerate(data['extra_roles'], 1): text += f"{i}\\- {p['name']} ⭐\n"
    text += "\n━━━━━━━━━━━━━\n🌷 *المُسْتَمِعَاتُ* 🌷\n"
    if not data['listeners']: text += "لا يوجد\\.\\.\n"
    else:
        for i, p in enumerate(data['listeners'], 1): text += f"{i}\\- {p['name']} 🌿\n"
    return text

@bot.callback_query_handler(func=lambda call: True)
def handle_buttons(call):
    uid, uname, cid = call.from_user.id, call.from_user.first_name, call.message.chat.id
    is_admin = get_user_rank(cid, uid)
    if call.data == "reg_extra":
        if data['extra_locked'] and not is_admin:
            bot.answer_callback_query(call.id, "⚠️ التسجيل الإضافي مغلق حالياً", show_alert=True)
            return
        if not any(p['id'] == uid for p in data['extra_roles']): data['extra_roles'].append({'id': uid, 'name': uname})
        else: data['extra_roles'] = [p for p in data['extra_roles'] if p['id'] != uid]
        bot.answer_callback_query(call.id, "تم تحديث حالتكِ")
    elif call.data == "admin_refresh": pass
    elif call.data == "admin_reset" and is_admin: data['readers'], data['listeners'], data['extra_roles'] = [], [], []
    elif call.data == "user_del_self":
        data['readers'] = [p for p in data['readers'] if p['id'] != uid]
        data['listeners'] = [p for p in data['listeners'] if p['id'] != uid]
        data['extra_roles'] = [p for p in data['extra_roles'] if p['id'] != uid]
    elif call.data == "reg_read":
        if not any(p['id'] == uid for p in data['readers']): data['readers'].append({'id': uid, 'name': uname, 'done': False})
        data['listeners'] = [p for p in data['listeners'] if p['id'] != uid]
    elif call.data == "reg_listen":
        if not any(p['id'] == uid for p in data['listeners']): data['listeners'].append({'id': uid, 'name': uname})
        data['readers'] = [p for p in data['readers'] if p['id'] != uid]
    elif call.data == "toggle_lock" and is_admin: data['is_open'] = not data['is_open']
    elif call.data == "toggle_extra_lock" and is_admin: data['extra_locked'] = not data['extra_locked']
    try: bot.edit_message_text(build_report_text(), cid, call.message.message_id, parse_mode="MarkdownV2", reply_markup=generate_markup(cid, uid))
    except: pass

@bot.message_handler(commands=['start'])
def start_bot(m):
    if not get_user_rank(m.chat.id, m.from_user.id): return
    msg = bot.send_message(m.chat.id, "📝 ما هي السورة الحالية؟")
    bot.register_next_step_handler(msg, save_surah_and_send_list)

def save_surah_and_send_list(m):
    data['current_surah'] = m.text
    bot.send_message(m.chat.id, build_report_text(), parse_mode="MarkdownV2", reply_markup=generate_markup(m.chat.id, m.from_user.id))

if __name__ == "__main__":
    keep_alive()
    bot.remove_webhook() # أهم سطر لحل مشكلة Conflict 409
    time.sleep(2)
    bot.infinity_polling(skip_pending=True) # يتجاهل الطلبات القديمة المعلقة
