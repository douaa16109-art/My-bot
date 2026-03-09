import telebot
from telebot import types
import time
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "Bot is Online with Ordering System!"

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

TOKEN = '8684986706:AAF6pkJQ8a4N3XeecnnJOXhsJpr8z7gv8bs'
bot = telebot.TeleBot(TOKEN, threaded=True)

# قاعدة البيانات المؤقتة
data = {
    'readers': [], 
    'listeners': [], 
    'extra_roles': [], 
    'is_open': True, 
    'extra_locked': False, 
    'current_surah': "لم تحدد بعد"
}

# دالة لتنظيف النص من الحروف التي تسبب خطأ 400
def clean_txt(text):
    chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in chars:
        text = text.replace(char, f"\\{char}")
    return text

def get_user_rank(chat_id, user_id):
    try:
        if chat_id > 0: return True
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ['administrator', 'creator']
    except: return False

def build_menu(chat_id, user_id):
    m = types.InlineKeyboardMarkup(row_width=2)
    is_admin = get_user_rank(chat_id, user_id)
    m.add(types.InlineKeyboardButton("🔄 اختيار الحالة (قارئة/مستمعة)", callback_data="choose_status"))
    m.add(types.InlineKeyboardButton("🗑️ حذف اسمي", callback_data="user_del"),
          types.InlineKeyboardButton("✅ أتممت القراءة", callback_data="set_done"))
    extra_txt = "🌿 تفعيل الإضافي" if not data['extra_locked'] else "🔒 الإضافي مغلق"
    m.add(types.InlineKeyboardButton(extra_txt, callback_data="reg_extra"))
    if is_admin:
        m.add(types.InlineKeyboardButton("⚙️ إعدادات المشرفات ⚙️", callback_data="admin_zone"))
    m.add(types.InlineKeyboardButton("🔄 تحديث القائمة", callback_data="refresh"))
    return m

def get_text():
    t = "❄️ *بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ* ❄️\n🌿 *مَجْلِسُ تِلَاوَةِ القُرْآنِ الكَرِيمِ* 🌿\n\n"
    t += f"📍 *السُّورَةُ: {clean_txt(data['current_surah'])}*\n━━━━━━━━━━━━━\n\n"
    t += "📖 *القارئات:*\n"
    if not data['readers']: t += "⏳ في انتظار التسجيل\\.\\.\n"
    else:
        for i, p in enumerate(data['readers'], 1): 
            t += f"{i}\\- {clean_txt(p['name'])} {'✅' if p['done'] else '⏳'}\n"
    t += "\n✨ *الأدوار الإضافية:*\n"
    if not data['extra_roles']: t += "لا يوجد إضافي\\.\n"
    else:
        for i, p in enumerate(data['extra_roles'], 1): t += f"{i}\\- {clean_txt(p['name'])} ⭐\n"
    t += "\n🎧 *المستمعات:*\n"
    if not data['listeners']: t += "لا يوجد\\.\n"
    else:
        for i, p in enumerate(data['listeners'], 1): t += f"{i}\\- {clean_txt(p['name'])} 🌿\n"
    return t

@bot.callback_query_handler(func=lambda call: True)
def handle_calls(call):
    uid, uname, cid = call.from_user.id, call.from_user.first_name, call.message.chat.id
    is_admin = get_user_rank(cid, uid)

    if call.data == "choose_status":
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
        if not any(p['id'] == uid for p in data['extra_roles']): data['extra_roles'].append({'id': uid, 'name': uname})
        else: data['extra_roles'] = [p for p in data['extra_roles'] if p['id'] != uid]

    elif call.data == "admin_zone" and is_admin:
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("↕️ إعادة الترتيب", callback_data="order_menu"))
        m.add(types.InlineKeyboardButton("✍️ تغيير السورة", callback_data="set_surah"))
        m.add(types.InlineKeyboardButton("🧨 تصفير القائمة", callback_data="reset_all"))
        m.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="refresh"))
        bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=m)
        return

    elif call.data == "order_menu" and is_admin:
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("📖 قائمة القارئات", callback_data="list_to_order:readers"),
              types.InlineKeyboardButton("✨ الأدوار الإضافية", callback_data="list_to_order:extra_roles"))
        m.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="admin_zone"))
        bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=m)
        return

    elif call.data.startswith("list_to_order:") and is_admin:
        list_type = call.data.split(":")[1]
        m = types.InlineKeyboardMarkup()
        for i, p in enumerate(data[list_type]):
            m.add(types.InlineKeyboardButton(f"{p['name']}", callback_data=f"pick_user:{list_type}:{i}"))
        m.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="order_menu"))
        bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=m)
        return

    elif call.data.startswith("pick_user:") and is_admin:
        _, list_type, index = call.data.split(":")
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("🔼 رفع", callback_data=f"move:{list_type}:{index}:up"),
              types.InlineKeyboardButton("🔽 خفض", callback_data=f"move:{list_type}:{index}:down"))
        m.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data=f"list_to_order:{list_type}"))
        bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=m)
        return

    elif call.data.startswith("move:") and is_admin:
        _, list_type, index, direction = call.data.split(":")
        idx = int(index)
        target_list = data[list_type]
        if direction == "up" and idx > 0:
            target_list[idx], target_list[idx-1] = target_list[idx-1], target_list[idx]
        elif direction == "down" and idx < len(target_list) - 1:
            target_list[idx], target_list[idx+1] = target_list[idx+1], target_list[idx]
        bot.answer_callback_query(call.id, "تم التغيير ✅")
        # العودة لقائمة الأسماء لإكمال الترتيب
        handle_calls(types.CallbackQuery(call.id, call.from_user, call.message, call.chat_instance, f"list_to_order:{list_type}"))
        return

    elif call.data == "set_done":
        for p in data['readers']:
            if p['id'] == uid: p['done'] = True
    elif call.data == "user_del":
        for l in [data['readers'], data['listeners'], data['extra_roles']]:
            l[:] = [p for p in l if p['id'] != uid]
    elif call.data == "reset_all" and is_admin:
        data['readers'], data['listeners'], data['extra_roles'] = [], [], []
    elif call.data == "set_surah" and is_admin:
        msg = bot.send_message(cid, "📝 أرسلي اسم السورة الجديدة:")
        bot.register_next_step_handler(msg, update_surah)
        return

    try:
        bot.edit_message_text(get_text(), cid, call.message.message_id, parse_mode="MarkdownV2", reply_markup=build_menu(cid, uid))
        bot.answer_callback_query(call.id, "تم ✅")
    except Exception as e:
        bot.answer_callback_query(call.id)

def update_surah(m):
    data['current_surah'] = m.text
    bot.send_message(m.chat.id, "✅ تم التحديث، اضغطي تحديث القائمة.")

@bot.message_handler(commands=['start'])
def start(m):
    if get_user_rank(m.chat.id, m.from_user.id):
        bot.send_message(m.chat.id, get_text(), parse_mode="MarkdownV2", reply_markup=build_menu(m.chat.id, m.from_user.id))

if __name__ == "__main__":
    keep_alive()
    bot.remove_webhook()
    time.sleep(1)
    bot.infinity_polling(skip_pending=True)
