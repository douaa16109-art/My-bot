import telebot
from telebot import types
import time
from datetime import datetime
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "Bot is Online with Your Private Phrases!"

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

TOKEN = '8684986706:AAF6pkJQ8a4N3XeecnnJOXhsJpr8z7gv8bs'
bot = telebot.TeleBot(TOKEN, threaded=True)

data = {
    'readers': [], 'listeners': [], 'extra_roles': [], 
    'is_open': True, 'current_surah': "لم تحدد بعد"
}

def esc(text):
    chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in chars: text = text.replace(char, f"\\{char}")
    return text

def get_user_rank(chat_id, user_id):
    try:
        if chat_id > 0: return True
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ['administrator', 'creator']
    except: return False

def build_menu(chat_id, user_id):
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(types.InlineKeyboardButton("📝 سجل اسمي", callback_data="reg_read"),
          types.InlineKeyboardButton("❌ احذف اسمي", callback_data="user_del"))
    m.add(types.InlineKeyboardButton("✅ قرأت", callback_data="set_done"),
          types.InlineKeyboardButton("🎧 مستمعة", callback_data="reg_listen"))
    m.add(types.InlineKeyboardButton("🌸 معتذرة (إضافي)", callback_data="reg_extra"))
    m.add(types.InlineKeyboardButton("🔄 إعادة إرسال القائمة", callback_data="resend_list"))
    if get_user_rank(chat_id, user_id):
        m.add(types.InlineKeyboardButton("⚙️ إعدادات المشرفات", callback_data="admin_zone"))
    return m

def get_text():
    now = datetime.now()
    miladi = now.strftime("%d/%m/%Y")
    
    # هنا عباراتكِ الخاصة التي طلبتِ عدم حذفها
    t = f"❄️ *بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ* ❄️\n🌿 *مَجْلِسُ تِلَاوَةِ القُرْآنِ الكَرِيمِ* 🌿\n\n"
    t += f"🗓️ {esc(miladi)} م\n"
    t += f"📍 *السُّورَةُ الحَالِيَّةُ: {esc(data['current_surah'])}*\n"
    t += "━━━━━━━━━━━━━━\n\n"
    
    t += "📖 *القارئات:*\n"
    if not data['readers']: t += "⏳ في انتظار التسجيل\\.\\.\n"
    else:
        for i, p in enumerate(data['readers'], 1):
            status = "✅" if p['done'] else "⏳"
            t += f"{i}\\- [{esc(p['name'])}](tg://user?id={p['id']}) {status}\n"
            
    t += "\n✨ *الأدوار الإضافية:*\n"
    if not data['extra_roles']: t += "لا يوجد إضافي\\.\n"
    else:
        for i, p in enumerate(data['extra_roles'], 1):
            t += f"{i}\\- [{esc(p['name'])}](tg://user?id={p['id']}) ⭐\n"

    t += "\n🎧 *المستمعات:*\n"
    if not data['listeners']: t += "لا يوجد مستمعات حالياً\\.\n"
    else:
        for i, p in enumerate(data['listeners'], 1):
            t += f"{i}\\- [{esc(p['name'])}](tg://user?id={p['id']}) 🌿\n"
    
    t += "\n━━━━━━━━━━━━━━\n"
    # عبارة الختام الخاصة بكِ
    t += "اللهم اجعلنا ممن يقال لهم:\n*(اقرأ وارتقِ ورتل كما كنت ترتل في الدنيا)*"
    return t

@bot.callback_query_handler(func=lambda call: True)
def handle_calls(call):
    uid, uname, cid = call.from_user.id, call.from_user.first_name, call.message.chat.id
    is_admin = get_user_rank(cid, uid)

    if call.data == "resend_list":
        try: bot.delete_message(cid, call.message.message_id)
        except: pass
        bot.send_message(cid, get_text(), parse_mode="MarkdownV2", reply_markup=build_menu(cid, uid))
        return

    # نظام إعادة الترتيب (الرفع والخفض)
    elif call.data == "admin_zone" and is_admin:
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("↕️ رفع/خفض الأسماء", callback_data="order_menu"))
        m.add(types.InlineKeyboardButton("✍️ تغيير السورة", callback_data="set_surah"))
        m.add(types.InlineKeyboardButton("🧨 تصفير شامل", callback_data="reset_all"))
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
        l_type = call.data.split(":")[1]
        m = types.InlineKeyboardMarkup()
        for i, p in enumerate(data[l_type]):
            m.add(types.InlineKeyboardButton(f"{p['name']}", callback_data=f"pick_u:{l_type}:{i}"))
        m.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="order_menu"))
        bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=m)
        return

    elif call.data.startswith("pick_u:") and is_admin:
        _, l_type, idx = call.data.split(":")
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("🔼 رفع", callback_data=f"move:{l_type}:{idx}:up"),
              types.InlineKeyboardButton("🔽 خفض", callback_data=f"move:{l_type}:{idx}:down"))
        m.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data=f"list_to_order:{l_type}"))
        bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=m)
        return

    elif call.data.startswith("move:") and is_admin:
        _, l_type, idx, direct = call.data.split(":")
        idx = int(idx)
        t_list = data[l_type]
        if direct == "up" and idx > 0:
            t_list[idx], t_list[idx-1] = t_list[idx-1], t_list[idx]
        elif direct == "down" and idx < len(t_list) - 1:
            t_list[idx], t_list[idx+1] = t_list[idx+1], t_list[idx]
        bot.answer_callback_query(call.id, "تم التغيير ✅")
        handle_calls(types.CallbackQuery(call.id, call.from_user, call.message, call.chat_instance, f"list_to_order:{l_type}"))
        return

    # تسجيل الأسماء
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
    elif call.data == "set_done":
        for p in data['readers']:
            if p['id'] == uid: p['done'] = True
    elif call.data == "user_del":
        for l in [data['readers'], data['listeners'], data['extra_roles']]:
            l[:] = [p for p in l if p['id'] != uid]
    elif call.data == "reset_all" and is_admin:
        data['readers'], data['listeners'], data['extra_roles'] = [], [], []
    elif call.data == "set_surah" and is_admin:
        msg = bot.send_message(cid, "📝 أرسلي اسم السورة:")
        bot.register_next_step_handler(msg, update_surah)
        return

    try:
        bot.edit_message_text(get_text(), cid, call.message.message_id, parse_mode="MarkdownV2", reply_markup=build_menu(cid, uid), disable_web_page_preview=True)
    except: pass

def update_surah(m):
    data['current_surah'] = m.text
    bot.send_message(m.chat.id, "✅ تم التحديث.")

@bot.message_handler(commands=['start'])
def start(m):
    if get_user_rank(m.chat.id, m.from_user.id):
        bot.send_message(m.chat.id, get_text(), parse_mode="MarkdownV2", reply_markup=build_menu(m.chat.id, m.from_user.id), disable_web_page_preview=True)

if __name__ == "__main__":
    keep_alive()
    bot.remove_webhook()
    time.sleep(1)
    bot.infinity_polling(skip_pending=True)
