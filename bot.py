import telebot
from telebot import types
import time
from flask import Flask
from threading import Thread

# --- سيرفر Flask لضمان استمرار العمل ---
app = Flask('')
@app.route('/')
def home(): return "Bot is Online!"

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

# --- التوكن الجديد الخاص بكِ ---
TOKEN = '8684986706:AAF6pkJQ8a4N3XeecnnJOXhsJpr8z7gv8bs'
bot = telebot.TeleBot(TOKEN, threaded=True)

# ذاكرة البيانات (سيتم تصفيرها مع كل إعادة تشغيل للسيرفر)
data = {
    'readers': [], 
    'listeners': [], 
    'extra_roles': [], 
    'is_open': True, 
    'extra_locked': False, 
    'current_surah': "لم تحدد بعد"
}

def get_user_rank(chat_id, user_id):
    try:
        if chat_id > 0: return True
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ['administrator', 'creator']
    except: return False

def build_menu(chat_id, user_id):
    m = types.InlineKeyboardMarkup(row_width=2)
    is_admin = get_user_rank(chat_id, user_id)
    
    # أزرار الأعضاء والمشرفات
    m.add(types.InlineKeyboardButton("🔄 اختيار الحالة (قارئة/مستمعة)", callback_data="choose_status"))
    m.add(types.InlineKeyboardButton("🗑️ حذف اسمي فقط", callback_data="user_del"),
          types.InlineKeyboardButton("✅ أتممت القراءة", callback_data="set_done"))
    
    # زر الإضافي المستقل (الذي طلبتِ عودته)
    extra_txt = "🌿 تفعيل الإضافي" if not data['extra_locked'] else "🌿 الإضافي (مغلق)"
    m.add(types.InlineKeyboardButton(extra_txt, callback_data="reg_extra"))

    if is_admin:
        # أزرار التحكم الخاصة بالمشرفات فقط
        m.add(types.InlineKeyboardButton("🔄 تحديث القائمة", callback_data="refresh"),
              types.InlineKeyboardButton("📖 تغيير السورة", callback_data="set_surah"))
        
        lock_btn = "🔒 إغلاق التسجيل" if data['is_open'] else "🔓 فتح التسجيل"
        extra_lock = "🔒 قفل الإضافي" if not data['extra_locked'] else "🔓 فتح الإضافي"
        
        m.add(types.InlineKeyboardButton(lock_btn, callback_data="toggle_lock"),
              types.InlineKeyboardButton(extra_lock, callback_data="toggle_extra"))
        
        m.add(types.InlineKeyboardButton("🧨 تصفير شامل", callback_data="reset"),
              types.InlineKeyboardButton("⚙️ إدارة الأسماء والترتيب", callback_data="manage"))
    return m

def get_text():
    status = "✅ مفتوحة" if data['is_open'] else "❌ مغلقة"
    t = "❄️ *بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ* ❄️\n🌿 *مَجْلِسُ تِلَاوَةِ القُرْآنِ الكَرِيمِ* 🌿\n\n"
    t += ">📖 **اعْلَمِي رَعَاكِ اللهُ؛ أنَّ حُضوركِ لهذا المجلسِ محضُ توفيقٍ واصطفاءٍ من ربّكِ\\.\\. فكم من محرومٍ والقرآنُ بين يديه، وكم من مُوفّقٍ يُساقُ الخيرُ إليه\\!**\n\n"
    t += f"━━━━━━━━━━━━━\nحالة القائمة الآن: {status}\n━━━━━━━━━━━━━\n\n"
    t += f"📍 *السُّورَةُ الحَالِيَّةُ: {data['current_surah']}*\n━━━━━━━━━━━━━\n\n"
    
    t += "🌷 *قَائِمَةُ القَارِئَاتِ* 🌷\n"
    if not data['readers']: t += "لا يوجد مسجلات بعد\\.\\.\n"
    else:
        for i, p in enumerate(data['readers'], 1):
            t += f"{i}\\- {p['name']} {'✅' if p['done'] else '⏳'}\n"
            
    t += "\n🌿 *الأدوار الإضافية* 🌿\n"
    if not data['extra_roles']: t += "لا يوجد مسجلات بعد\\.\\.\n"
    else:
        for i, p in enumerate(data['extra_roles'], 1):
            t += f"{i}\\- {p['name']} ⭐\n"

    t += "\n━━━━━━━━━━━━━\n🌷 *المُسْتَمِعَاتُ* 🌷\n"
    if not data['listeners']: t += "لا يوجد\\.\\.\n"
    else:
        for i, p in enumerate(data['listeners'], 1):
            t += f"{i}\\- {p['name']} 🌿\n"
    return t

@bot.callback_query_handler(func=lambda call: True)
def handle(call):
    uid, uname, cid = call.from_user.id, call.from_user.first_name, call.message.chat.id
    is_admin = get_user_rank(cid, uid)

    # منطق زر الإضافي
    if call.data == "reg_extra":
        if data['extra_locked'] and not is_admin:
            bot.answer_callback_query(call.id, "⚠️ عذراً، التسجيل الإضافي مغلق حالياً", show_alert=True)
            return
        if not any(p['id'] == uid for p in data['extra_roles']):
            data['extra_roles'].append({'id': uid, 'name': uname})
        else:
            data['extra_roles'] = [p for p in data['extra_roles'] if p['id'] != uid]
        bot.answer_callback_query(call.id, "تم تحديث حالتكِ")

    elif call.data == "choose_status":
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("📖 تسجيل كقارئة", callback_data="reg_read"),
              types.InlineKeyboardButton("🎧 تسجيل كمستمعة", callback_data="reg_listen"))
        bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=m)
        return

    elif call.data == "reg_read" and data['is_open']:
        if not any(p['id'] == uid for p in data['readers']):
            data['readers'].append({'id': uid, 'name': uname, 'done': False})
            data['listeners'] = [p for p in data['listeners'] if p['id'] != uid]

    elif call.data == "reg_listen" and data['is_open']:
        if not any(p['id'] == uid for p in data['listeners']):
            data['listeners'].append({'id': uid, 'name': uname})
            data['readers'] = [p for p in data['readers'] if p['id'] != uid]

    elif call.data == "set_done":
        for p in data['readers']:
            if p['id'] == uid: p['done'] = True

    elif call.data == "user_del":
        data['readers'] = [p for p in data['readers'] if p['id'] != uid]
        data['listeners'] = [p for p in data['listeners'] if p['id'] != uid]
        data['extra_roles'] = [p for p in data['extra_roles'] if p['id'] != uid]

    elif call.data == "reset" and is_admin:
        data['readers'], data['listeners'], data['extra_roles'] = [], [], []

    elif call.data == "toggle_lock" and is_admin:
        data['is_open'] = not data['is_open']
    
    elif call.data == "toggle_extra" and is_admin:
        data['extra_locked'] = not data['extra_locked']

    try:
        bot.edit_message_text(get_text(), cid, call.message.message_id, parse_mode="MarkdownV2", reply_markup=build_menu(cid, uid))
    except: pass

@bot.message_handler(commands=['start'])
def start(m):
    if not get_user_rank(m.chat.id, m.from_user.id): return
    msg = bot.send_message(m.chat.id, "📝 ما هي السورة الحالية؟")
    bot.register_next_step_handler(msg, finish_start)

def finish_start(m):
    data['current_surah'] = m.text
    bot.send_message(m.chat.id, get_text(), parse_mode="MarkdownV2", reply_markup=build_menu(m.chat.id, m.from_user.id))

if __name__ == "__main__":
    keep_alive()
    bot.remove_webhook()
    time.sleep(1)
    bot.infinity_polling(skip_pending=True)
