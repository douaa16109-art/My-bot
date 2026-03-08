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
        # سطر زر الأدوار الإضافية
        markup.add(types.InlineKeyboardButton("⚙️ إدارة الأسماء والترتيب", callback_data="admin_manage_panel"))
    return markup

def build_report_text():
    status = "✅ مفتوحة" if data['is_open'] else "❌ مغلقة"
    text = "❄️ *بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ* ❄️\n"
    text += "🌿 *مَجْلِسُ تِلَاوَةِ القُرْآنِ الكَرِيمِ* 🌿\n\n"
    text += ">📖 **اعْلَمِي رَعَاكِ اللهُ؛ أنَّ حُضوركِ لهذا المجلسِ محضُ توفيقٍ واصطفاءٍ من ربّكِ\\.\\. فكم من محرومٍ والقرآنُ بين يديه، وكم من مُوفّقٍ يُساقُ الخيرُ إليه\\!**\n\n"
    text += "━━━━━━━━━━━━━\n"
    text += f"حالة القائمة الآن: {status}\n"
    text += "━━━━━━━━━━━━━\n\n"
    text += f"📍 *السُّورَةُ الحَالِيَّةُ: {data['current_surah']}*\n"
    text += "━━━━━━━━━━━━━\n\n"
    text += "🌷 *قَائِمَةُ القَارِئَاتِ* 🌷\n"
    if not data['readers']: text += "لا يوجد مسجلات بعد\\.\\.\n"
    else:
        for i, p in enumerate(data['readers'], 1):
            icon = "✅" if p['done'] else "⏳"
            text += f"{i}\\- {p['name']} {icon}\n"
    text += "\n━━━━━━━━━━━━━\n"
    text += "🌷 *المُسْتَمِعَاتُ* 🌷\n"
    if not data['listeners']: text += "لا يوجد\\.\\.\n"
    else:
        for i, p in enumerate(data['listeners'], 1):
            text += f"{i}\\- {p['name']} 🌿\n"
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

    if call.data == "admin_refresh":
        bot.edit_message_text(build_report_text(), cid, call.message.message_id, parse_mode="MarkdownV2", reply_markup=generate_markup(cid, uid))
        return

    # --- الأسطر التي كانت مفقودة للأدوار الإضافية ---
    if is_admin:
        if call.data == "admin_manage_panel":
            m = types.InlineKeyboardMarkup()
            for p in data['readers'] + data['listeners']:
                m.add(types.InlineKeyboardButton(f"👤 {p['name']}", callback_data=f"opts_{p['id']}"))
            m.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="admin_refresh"))
            bot.edit_message_text("⚙️ تحكمي في الأسماء والترتيب:", cid, call.message.message_id, reply_markup=m)
            return
        elif call.data.startswith("opts_"):
            tid = int(call.data.split("_")[1])
            m = types.InlineKeyboardMarkup()
            m.add(types.InlineKeyboardButton("🔼 رفع", callback_data=f"up_{tid}"), types.InlineKeyboardButton("🔽 خفض", callback_data=f"down_{tid}"))
            m.add(types.InlineKeyboardButton("🔄 تبديل", callback_data=f"swap_{tid}"), types.InlineKeyboardButton("🗑️ حذف", callback_data=f"fdel_{tid}"))
            m.add(types.InlineKeyboardButton("🔙 عودة", callback_data="admin_manage_panel"))
            bot.edit_message_text("تعديل العضوة:", cid, call.message.message_id, reply_markup=m)
            return
        elif call.data.startswith(("up_", "down_")):
            act, tid = call.data.split("_")
            tid = int(tid)
            lst = data['readers'] if any(p['id'] == tid for p in data['readers']) else data['listeners']
            idx = next(i for i, p in enumerate(lst) if p['id'] == tid)
            if act == "up" and idx > 0: lst[idx], lst[idx-1] = lst[idx-1], lst[idx]
            elif act == "down" and idx < len(lst)-1: lst[idx], lst[idx+1] = lst[idx+1], lst[idx]
        elif call.data.startswith("swap_"):
            tid = int(call.data.split("_")[1])
            r = next((p for p in data['readers'] if p['id'] == tid), None)
            if r: data['readers'].remove(r); data['listeners'].append({'id': r['id'], 'name': r['name']})
            else:
                l = next((p for p in data['listeners'] if p['id'] == tid), None)
                if l: data['listeners'].remove(l); data['readers'].append({'id': l['id'], 'name': l['name'], 'done': False})
        elif call.data.startswith("fdel_"):
            tid = int(call.data.split("_")[1])
            data['readers'] = [p for p in data['readers'] if p['id'] != tid]
            data['listeners'] = [p for p in data['listeners'] if p['id'] != tid]
        elif call.data == "admin_reset":
            data['readers'], data['listeners'] = [], []
        elif call.data == "toggle_lock":
            data['is_open'] = not data['is_open']
    
    # منطق تسجيل الأعضاء
    if call.data == "choose_status" and data['is_open']:
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("📖 تسجيل كقارئة", callback_data="reg_read"), types.InlineKeyboardButton("🎧 تسجيل كمستمعة", callback_data="reg_listen"))
        bot.edit_message_text("اختاري حالتكِ:", cid, call.message.message_id, reply_markup=m)
        return
    elif call.data == "reg_read":
        if not any(p['id'] == uid for p in data['readers']): data['readers'].append({'id': uid, 'name': uname, 'done': False})
        data['listeners'] = [p for p in data['listeners'] if p['id'] != uid]
    elif call.data == "reg_listen":
        if not any(p['id'] == uid for p in data['listeners']): data['listeners'].append({'id': uid, 'name': uname})
        data['readers'] = [p for p in data['readers'] if p['id'] != uid]
    elif call.data == "set_done":
        for p in data['readers']:
            if p['id'] == uid: p['done'] = True
    elif call.data == "user_del_self":
        data['readers'] = [p for p in data['readers'] if p['id'] != uid]
        data['listeners'] = [p for p in data['listeners'] if p['id'] != uid]

    bot.edit_message_text(build_report_text(), cid, call.message.message_id, parse_mode="MarkdownV2", reply_markup=generate_markup(cid, uid))

if __name__ == "__main__":
    keep_alive()
    bot.remove_webhook()
    time.sleep(1)
    bot.infinity_polling(timeout=20)
