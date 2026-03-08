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

TOKEN = '8753124430:AAHjTw4-KRaNUSE5OznIwMjzFaXN6ll2FIM'
bot = telebot.TeleBot(TOKEN)

# الذاكرة (أضفنا قائمة للأدوار الإضافية وحالة القفل الخاصة بها)
data = {
    'readers': [], 
    'listeners': [], 
    'extra_roles': [], # قائمة الأدوار الإضافية
    'is_open': True, 
    'extra_locked': False, # قفل الأدوار الإضافية
    'current_surah': "لم تحدد بعد"
}

def get_user_rank(chat_id, user_id):
    try:
        if chat_id > 0: return True 
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ['administrator', 'creator']
    except: return False

def generate_markup(chat_id, user_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    is_admin = get_user_rank(chat_id, user_id)
    
    # أزرار الأعضاء
    markup.add(types.InlineKeyboardButton("🔄 اختيار الحالة", callback_data="choose_status"))
    
    # زر الأدوار الإضافية (يظهر للجميع، لكن يعمل حسب القفل)
    markup.add(types.InlineKeyboardButton("🌟 الأدوار الإضافية", callback_data="extra_roles_menu"))
    
    markup.add(types.InlineKeyboardButton("✅ أتممت القراءة", callback_data="set_done"),
               types.InlineKeyboardButton("🗑️ حذف اسمي فقط", callback_data="user_del_self"))
    
    if is_admin:
        markup.add(types.InlineKeyboardButton("🔃 تحديث القائمة", callback_data="admin_refresh"),
                   types.InlineKeyboardButton("📖 تغيير السورة", callback_data="admin_set_surah"))
        
        lock_text = "🔓 فتح القائمة" if not data['is_open'] else "🔒 إغلاق القائمة"
        # زر قفل/فتح الأدوار الإضافية للمشرفات
        extra_lock_text = "🔓 فتح الأدوار" if data['extra_locked'] else "🔒 قفل الأدوار"
        
        markup.add(types.InlineKeyboardButton(lock_text, callback_data="toggle_lock"),
                   types.InlineKeyboardButton(extra_lock_text, callback_data="toggle_extra_lock"))
        
        markup.add(types.InlineKeyboardButton("🧨 تصفير القائمة", callback_data="admin_reset"),
                   types.InlineKeyboardButton("⚙️ إدارة الأسماء والترتيب", callback_data="admin_manage_panel"))
        
    return markup

def build_report_text():
    status = "✅ مفتوحة" if data['is_open'] else "❌ مغلقة"
    e_status = "❌ مقفلة" if data['extra_locked'] else "✅ متاحة"
    
    text = "❄️ *بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ* ❄️\n🌿 *مَجْلِسُ تِلَاوَةِ القُرْآنِ الكَرِيمِ* 🌿\n\n"
    text += ">📖 **اعْلَمِي رَعَاكِ اللهُ؛ أنَّ حُضوركِ لهذا المجلسِ محضُ توفيقٍ واصطفاءٍ من ربّكِ\\.\\. فكم من محرومٍ والقرآنُ بين يديه، وكم من مُوفّقٍ يُساقُ الخيرُ إليه\\!**\n\n"
    text += f"━━━━━━━━━━━━━\nحالة القائمة: {status} | الأدوار: {e_status}\n━━━━━━━━━━━━━\n\n"
    text += f"📍 *السُّورَةُ الحَالِيَّةُ: {data['current_surah']}*\n━━━━━━━━━━━━━\n\n"
    
    text += "🌷 *قَائِمَةُ القَارِئَاتِ* 🌷\n"
    if not data['readers']: text += "لا يوجد مسجلات\\.\\.\n"
    else:
        for i, p in enumerate(data['readers'], 1):
            text += f"{i}\\- {p['name']} {'✅' if p['done'] else '⏳'}\n"
            
    text += "\n✨ *أصحاب الأدوار الإضافية* ✨\n"
    if not data['extra_roles']: text += "لا يوجد\\.\\.\n"
    else:
        for i, p in enumerate(data['extra_roles'], 1):
            text += f"{i}\\- {p['name']} ⭐\n"

    text += "\n━━━━━━━━━━━━━\n🌷 *المُسْتَمِعَاتُ* 🌷\n"
    if not data['listeners']: text += "لا يوجد\\.\\.\n"
    else:
        for i, p in enumerate(data['listeners'], 1):
            text += f"{i}\\- {p['name']} 🌿\n"
    return text

@bot.callback_query_handler(func=lambda call: True)
def handle_buttons(call):
    uid, uname, cid = call.from_user.id, call.from_user.first_name, call.message.chat.id
    is_admin = get_user_rank(cid, uid)

    # منطق الأدوار الإضافية
    if call.data == "extra_roles_menu":
        if data['extra_locked'] and not is_admin:
            bot.answer_callback_query(call.id, "⚠️ عذراً، الأدوار الإضافية مقفلة الآن.", show_alert=True)
            return
        # إضافة العضو للأدوار الإضافية
        if not any(p['id'] == uid for p in data['extra_roles']):
            data['extra_roles'].append({'id': uid, 'name': uname})
            bot.answer_callback_query(call.id, "✅ تم تسجيلك في الأدوار الإضافية")
        else:
            bot.answer_callback_query(call.id, "أنتِ مسجلة بالفعل!")

    elif call.data == "toggle_extra_lock" and is_admin:
        data['extra_locked'] = not data['extra_locked']
        bot.answer_callback_query(call.id, f"تم {'قفل' if data['extra_locked'] else 'فتح'} الأدوار الإضافية")

    # إدارة الأسماء والترتيب (للمشرفات)
    elif is_admin and call.data == "admin_manage_panel":
        m = types.InlineKeyboardMarkup()
        for p in data['readers'] + data['listeners'] + data['extra_roles']:
            m.add(types.InlineKeyboardButton(f"👤 {p['name']}", callback_data=f"opts_{p['id']}"))
        m.add(types.InlineKeyboardButton("🔙 عودة", callback_data="admin_refresh"))
        bot.edit_message_text("⚙️ إدارة الأسماء:", cid, call.message.message_id, reply_markup=m)
        return

    # حذف وتصفير
    elif call.data == "admin_reset" and is_admin:
        data['readers'], data['listeners'], data['extra_roles'] = [], [], []
    elif call.data == "user_del_self":
        data['readers'] = [p for p in data['readers'] if p['id'] != uid]
        data['listeners'] = [p for p in data['listeners'] if p['id'] != uid]
        data['extra_roles'] = [p for p in data['extra_roles'] if p['id'] != uid]
    
    # باقي الأزرار المعروفة
    elif call.data == "toggle_lock" and is_admin:
        data['is_open'] = not data['is_open']
    elif call.data == "reg_read":
        if not any(p['id'] == uid for p in data['readers']): data['readers'].append({'id': uid, 'name': uname, 'done': False})
        data['listeners'] = [p for p in data['listeners'] if p['id'] != uid]
    elif call.data == "reg_listen":
        if not any(p['id'] == uid for p in data['listeners']): data['listeners'].append({'id': uid, 'name': uname})
        data['readers'] = [p for p in data['readers'] if p['id'] != uid]

    # تحديث الرسالة
    try:
        bot.edit_message_text(build_report_text(), cid, call.message.message_id, parse_mode="MarkdownV2", reply_markup=generate_markup(cid, uid))
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
    bot.remove_webhook()
    time.sleep(1)
    bot.infinity_polling()
