import telebot
from telebot import types
import time
from flask import Flask
from threading import Thread

# إعداد السيرفر للبقاء حياً
app = Flask('')
@app.route('/')
def home(): return "Bot is Online and Ready!"

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

# التوكن الجديد الخاص بكِ
TOKEN = '8684986706:AAF6pkJQ8a4N3XeecnnJOXhsJpr8z7gv8bs'
bot = telebot.TeleBot(TOKEN, threaded=True)

# قاعدة البيانات المؤقتة
data = {
    'readers': [], 
    'listeners': [], 
    'extra_roles': [], 
    'is_open': True, 
    'extra_locked': False, 
    'current_surah': "لم تُحدد بعد"
}

# وظيفة التحقق من الرتبة (مشرفة أو عضو)
def get_user_rank(chat_id, user_id):
    try:
        if chat_id > 0: return True # للخاص
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ['administrator', 'creator']
    except: return False

# بناء القائمة (الأزرار)
def build_menu(chat_id, user_id):
    m = types.InlineKeyboardMarkup(row_width=2)
    is_admin = get_user_rank(chat_id, user_id)
    
    # أزرار لجميع الأعضاء
    m.add(types.InlineKeyboardButton("🔄 اختيار الحالة (قارئة/مستمعة)", callback_data="choose_status"))
    m.add(types.InlineKeyboardButton("🗑️ حذف اسمي", callback_data="user_del"),
          types.InlineKeyboardButton("✅ أتممت القراءة", callback_data="set_done"))
    
    extra_txt = "🌿 تفعيل الإضافي" if not data['extra_locked'] else "🔒 الإضافي مغلق"
    m.add(types.InlineKeyboardButton(extra_txt, callback_data="reg_extra"))

    # أزرار للمشرفات فقط (تظهر للكل لكن لا تعمل إلا للمشرفات)
    if is_admin:
        m.add(types.InlineKeyboardButton("⚙️ إعدادات المشرفات ⚙️", callback_data="admin_zone"))
    
    m.add(types.InlineKeyboardButton("🔄 تحديث القائمة", callback_data="refresh"))
    return m

# نص القائمة
def get_text():
    t = "❄️ *بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ* ❄️\n🌿 *مَجْلِسُ تِلَاوَةِ القُرْآنِ الكَرِيمِ* 🌿\n\n"
    t += f"📍 *السُّورَةُ الحَالِيَّةُ: {data['current_surah']}*\n"
    t += f"💬 *حالة التسجيل:* {'✅ مفتوح' if data['is_open'] else '❌ مغلق'}\n"
    t += "━━━━━━━━━━━━━\n\n"
    
    t += "📖 *القارئات:*\n"
    if not data['readers']: t += "⏳ في انتظار التسجيل..\n"
    else:
        for i, p in enumerate(data['readers'], 1): 
            status = "✅" if p['done'] else "⏳"
            t += f"{i}\\- {p['name']} {status}\n"
            
    t += "\n🎧 *المستمعات:*\n"
    if not data['listeners']: t += "لا يوجد مستمعات حالياً..\n"
    else:
        for i, p in enumerate(data['listeners'], 1): t += f"{i}\\- {p['name']} 🌿\n"

    t += "\n✨ *الأدوار الإضافية:*\n"
    if not data['extra_roles']: t += "لا يوجد إضافي..\n"
    else:
        for i, p in enumerate(data['extra_roles'], 1): t += f"{i}\\- {p['name']} ⭐\n"
    
    return t

@bot.callback_query_handler(func=lambda call: True)
def handle_calls(call):
    uid = call.from_user.id
    uname = call.from_user.first_name
    cid = call.message.chat.id
    is_admin = get_user_rank(cid, uid)

    if call.data == "choose_status":
        if not data['is_open']:
            bot.answer_callback_query(call.id, "❌ التسجيل مغلق حالياً")
            return
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("📖 تسجيل كقارئة", callback_data="reg_read"),
              types.InlineKeyboardButton("🎧 تسجيل كمستمعة", callback_data="reg_listen"))
        m.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="refresh"))
        bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=m)
        return

    elif call.data == "reg_read":
        if not any(p['id'] == uid for p in data['readers']):
            data['readers'].append({'id': uid, 'name': uname, 'done': False})
            data['listeners'] = [p for p in data['listeners'] if p['id'] != uid]
    
    elif call.data == "reg_listen":
        if not any(p['id'] == uid for p in data['listeners']):
            data['listeners'].append({'id': uid, 'name': uname})
            data['readers'] = [p for p in data['readers'] if p['id'] != uid]

    elif call.data == "reg_extra":
        if data['extra_locked']:
            bot.answer_callback_query(call.id, "🔒 عذراً، الإضافي مغلق")
            return
        if not any(p['id'] == uid for p in data['extra_roles']): data['extra_roles'].append({'id': uid, 'name': uname})
        else: data['extra_roles'] = [p for p in data['extra_roles'] if p['id'] != uid]

    elif call.data == "set_done":
        for p in data['readers']:
            if p['id'] == uid: p['done'] = True

    elif call.data == "user_del":
        data['readers'] = [p for p in data['readers'] if p['id'] != uid]
        data['listeners'] = [p for p in data['listeners'] if p['id'] != uid]
        data['extra_roles'] = [p for p in data['extra_roles'] if p['id'] != uid]

    # قائمة المشرفات
    elif call.data == "admin_zone":
        if not is_admin:
            bot.answer_callback_query(call.id, "❌ هذا الزر للمشرفات فقط!")
            return
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("✍️ تغيير السورة", callback_data="set_surah"))
        m.add(types.InlineKeyboardButton("🔓/🔒 فتح-قفل التسجيل", callback_data="lock_reg"))
        m.add(types.InlineKeyboardButton("🔓/🔒 فتح-قفل الإضافي", callback_data="lock_extra"))
        m.add(types.InlineKeyboardButton("🧨 تصفير القائمة", callback_data="reset_all"))
        m.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="refresh"))
        bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=m)
        return

    elif call.data == "lock_reg" and is_admin:
        data['is_open'] = not data['is_open']
    elif call.data == "lock_extra" and is_admin:
        data['extra_locked'] = not data['extra_locked']
    elif call.data == "reset_all" and is_admin:
        data['readers'], data['listeners'], data['extra_roles'] = [], [], []
    elif call.data == "set_surah" and is_admin:
        msg = bot.send_message(cid, "📝 أرسلي اسم السورة الجديدة الآن:")
        bot.register_next_step_handler(msg, update_surah)
        return

    # تحديث الرسالة
    try:
        bot.edit_message_text(get_text(), cid, call.message.message_id, parse_mode="MarkdownV2", reply_markup=build_menu(cid, uid))
        bot.answer_callback_query(call.id, "تم التحديث ✅")
    except:
        bot.answer_callback_query(call.id)

def update_surah(m):
    data['current_surah'] = m.text
    bot.send_message(m.chat.id, "✅ تم تحديث اسم السورة، اضغطي 'تحديث القائمة' لتظهر للجميع.")

@bot.message_handler(commands=['start'])
def start(m):
    if get_user_rank(m.chat.id, m.from_user.id):
        bot.send_message(m.chat.id, get_text(), parse_mode="MarkdownV2", reply_markup=build_menu(m.chat.id, m.from_user.id))
    else:
        bot.reply_to(m, "❌ عذراً، تفعيل القائمة للمشرفات فقط.")

if __name__ == "__main__":
    keep_alive()
    bot.remove_webhook()
    time.sleep(1)
    bot.infinity_polling(skip_pending=True)
