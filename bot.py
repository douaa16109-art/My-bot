import telebot
from telebot import types
import time
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "Bot is Online!"

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

TOKEN = '8684986706:AAF6pkJQ8a4N3XeecnnJOXhsJpr8z7gv8bs'
bot = telebot.TeleBot(TOKEN, threaded=True)

data = {'readers': [], 'listeners': [], 'extra_roles': [], 'is_open': True, 'extra_locked': False, 'current_surah': "لم تحدد بعد"}

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
    m.add(types.InlineKeyboardButton("🗑️ حذف اسمي فقط", callback_data="user_del"),
          types.InlineKeyboardButton("✅ أتممت القراءة", callback_data="set_done"))
    
    extra_txt = "🌿 تفعيل الإضافي" if not data['extra_locked'] else "🌿 الإضافي (مغلق)"
    m.add(types.InlineKeyboardButton(extra_txt, callback_data="reg_extra"))

    if is_admin:
        m.add(types.InlineKeyboardButton("🔄 تحديث القائمة", callback_data="refresh"))
        m.add(types.InlineKeyboardButton("🔒 إغلاق التسجيل" if data['is_open'] else "🔓 فتح التسجيل", callback_data="toggle_lock"),
              types.InlineKeyboardButton("🔒 قفل الإضافي" if not data['extra_locked'] else "🔓 فتح الإضافي", callback_data="toggle_extra"))
        m.add(types.InlineKeyboardButton("🧨 تصفير شامل", callback_data="reset"))
    return m

def get_text():
    t = "❄️ *بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ* ❄️\n🌿 *مَجْلِسُ تِلَاوَةِ القُرْآنِ الكَرِيمِ* 🌿\n\n"
    t += f"📍 *السُّورَةُ: {data['current_surah']}*\n━━━━━━━━━━━━━\n\n"
    t += "🌷 *القارئات:*\n"
    if not data['readers']: t += "لا يوجد مسجلات..\n"
    else:
        for i, p in enumerate(data['readers'], 1): t += f"{i}\\- {p['name']} {'✅' if p['done'] else '⏳'}\n"
    t += "\n🌿 *الأدوار الإضافية:*\n"
    if not data['extra_roles']: t += "لا يوجد مسجلات..\n"
    else:
        for i, p in enumerate(data['extra_roles'], 1): t += f"{i}\\- {p['name']} ⭐\n"
    t += "\n🎧 *المستمعات:*\n"
    if not data['listeners']: t += "لا يوجد..\n"
    else:
        for i, p in enumerate(data['listeners'], 1): t += f"{i}\\- {p['name']} 🌿\n"
    return t

@bot.callback_query_handler(func=lambda call: True)
def handle(call):
    uid, uname, cid = call.from_user.id, call.from_user.first_name, call.message.chat.id
    
    if call.data == "choose_status":
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("📖 تسجيل كقارئة", callback_data="reg_read"),
              types.InlineKeyboardButton("🎧 تسجيل كمستمعة", callback_data="reg_listen"))
        m.add(types.InlineKeyboardButton("⬅️ رجوع للقائمة الأساسية", callback_data="refresh")) # هنا زر الرجوع
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

    elif call.data == "set_done":
        for p in data['readers']:
            if p['id'] == uid: p['done'] = True

    elif call.data == "user_del":
        data['readers'] = [p for p in data['readers'] if p['id'] != uid]
        data['listeners'] = [p for p in data['listeners'] if p['id'] != uid]
        data['extra_roles'] = [p for p in data['extra_roles'] if p['id'] != uid]

    elif call.data == "reset" and get_user_rank(cid, uid):
        data['readers'], data['listeners'], data['extra_roles'] = [], [], []

    elif call.data == "toggle_lock" and get_user_rank(cid, uid):
        data['is_open'] = not data['is_open']

    # تحديث القائمة (سواء ضغطت على تحديث أو رجوع أو أي زر آخر)
    try:
        bot.edit_message_text(get_text(), cid, call.message.message_id, parse_mode="MarkdownV2", reply_markup=build_menu(cid, uid))
        bot.answer_callback_query(call.id, "تم التحديث ✅")
    except:
        bot.answer_callback_query(call.id)

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
