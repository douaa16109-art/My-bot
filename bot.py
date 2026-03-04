import telebot
from telebot import types
from flask import Flask
from threading import Thread

# --- إعداد السيرفر لإبقاء البوت حياً ---
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
    'current_page': 0,
    'is_open': True,
    'extra_allowed': False,
    'page_step': 2 
}

def is_user_admin(chat_id, user_id):
    if chat_id > 0: return True 
    try:
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ['administrator', 'creator']
    except: return False

def generate_main_markup(chat_id, user_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📝 تسجيل كقارئة", callback_data="reg_read"),
        types.InlineKeyboardButton("🎧 تسجيل كمستمعة", callback_data="reg_listen")
    )
    
    if data['extra_allowed'] and data['is_open']:
        markup.add(types.InlineKeyboardButton("➕ تسجيل دور إضافي", callback_data="reg_extra"))
        
    markup.add(
        types.InlineKeyboardButton("✅ أتممت القراءة", callback_data="set_done"),
        types.InlineKeyboardButton("🗑️ حذف اسمي", callback_data="user_del")
    )
    
    if is_user_admin(chat_id, user_id):
        markup.add(
            types.InlineKeyboardButton("📊 تقرير الختام", callback_data="admin_report"),
            types.InlineKeyboardButton("🔔 تنبيه المتأخرات", callback_data="admin_remind")
        )
        lock_text = "🔓 فتح التسجيل" if not data['is_open'] else "🔒 إغلاق التسجيل"
        extra_text = "🚫 منع الأدوار الإضافية" if data['extra_allowed'] else "🌿 تفعيل الأدوار الإضافية"
        
        markup.add(types.InlineKeyboardButton(lock_text, callback_data="toggle_lock"))
        markup.add(types.InlineKeyboardButton(extra_text, callback_data="toggle_extra"))
        markup.add(types.InlineKeyboardButton("🧨 تصفير القائمة", callback_data="admin_reset"))
        markup.add(types.InlineKeyboardButton("⚙️ لوحة الحذف للمشرفات", callback_data="admin_del_panel"))
        
    return markup

def build_report_text():
    status = "✅ مفتوحة" if data['is_open'] else "❌ مغلقة"
    extra_status = "✅ مسموح" if data['extra_allowed'] else "🚫 ممنوع"
    text = f"❄ بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ ❄\n"
    text += f"🌿 **مَجْلِسُ تِلَاوَةِ القُرْآنِ الكَرِيمِ** 🌿\n"
    text += f"━━━━━━━━━━━━━\n"
    text += f"حالة القائمة: {status}\n"
    text += f"الأدوار الإضافية: {extra_status}\n"
    text += f"📍 الصفحة التالية: {data['current_page']}\n"
    text += f"━━━━━━━━━━━━━\n\n"
    
    text += "📖 **قائمة القارئات:**\n"
    if not data['readers']: text += "لا يوجد مسجلات..\n"
    else:
        for i, p in enumerate(data['readers'], 1):
            icon = "✅" if p['done'] else "⏳"
            text += f"{i}- {p['name']} (ص {p['range']}) {icon}\n"
            
    text += "\n🎧 **المستمعات:**\n"
    if not data['listeners']: text += "لا يوجد..\n"
    else:
        for i, p in enumerate(data['listeners'], 1):
            text += f"{i}- {p['name']} 🌿\n"
            
    return text

@bot.message_handler(commands=['start'])
def start_bot(m):
    bot.send_message(m.chat.id, "مرحباً بكِ في مَجْلِسِ التِّلَاوَةِ.", reply_markup=generate_main_markup(m.chat.id, m.from_user.id))

@bot.message_handler(func=lambda m: "بداية الوجه" in m.text)
def set_start_page(m):
    if is_user_admin(m.chat.id, m.from_user.id):
        nums = ''.join(filter(str.isdigit, m.text))
        if nums:
            data['current_page'] = int(nums)
            bot.send_message(m.chat.id, f"✅ تم ضبط البداية من ص {nums}\nكم صفحة لكل طالبة؟ (أرسلي الرقم فقط)")
            bot.register_next_step_handler(m, set_step)

def set_step(m):
    if m.text.isdigit():
        data['page_step'] = int(m.text)
        bot.send_message(m.chat.id, f"✅ تم الضبط: {m.text} صفحات لكل طالبة.", reply_markup=generate_main_markup(m.chat.id, m.from_user.id))

@bot.callback_query_handler(func=lambda call: True)
def handle_buttons(call):
    uid, uname, cid = call.from_user.id, call.from_user.first_name, call.message.chat.id
    
    if call.data in ["reg_read", "reg_listen", "reg_extra"] and not data['is_open']:
        bot.answer_callback_query(call.id, "⚠️ القائمة مغلقة حالياً.", show_alert=True)
        return

    if call.data == "reg_read":
        if any(p['id'] == uid for p in data['readers']):
            bot.answer_callback_query(call.id, "أنتِ مسجلة بالفعل!")
            return
        start_p = data['current_page']
        end_p = start_p + (data['page_step'] - 1)
        data['readers'].append({'id': uid, 'name': uname, 'range': f"{start_p}-{end_p}", 'done': False})
        data['current_page'] = end_p + 1
        
    elif call.data == "reg_extra":
        if not data['extra_allowed']: return
        start_p = data['current_page']
        end_p = start_p + (data['page_step'] - 1)
        data['readers'].append({'id': uid, 'name': f"{uname} (إضافي)", 'range': f"{start_p}-{end_p}", 'done': False})
        data['current_page'] = end_p + 1

    elif call.data == "reg_listen":
        if any(p['id'] == uid for p in data['listeners']): return
        data['listeners'].append({'id': uid, 'name': uname})
        
    elif call.data == "set_done":
        for p in data['readers']:
            if p['id'] == uid: p['done'] = True

    elif call.data == "user_del":
        data['readers'] = [p for p in data['readers'] if p['id'] != uid]
        data['listeners'] = [p for p in data['listeners'] if p['id'] != uid]
        bot.answer_callback_query(call.id, "✅ تم حذف اسمكِ من القائمة.")
            
    elif call.data == "admin_reset":
        if is_user_admin(cid, uid):
            data['readers'], data['listeners'] = [], []
            bot.answer_callback_query(call.id, "تم تصفير القائمة")

    elif call.data == "admin_remind":
        if is_user_admin(cid, uid):
            mentions = ""
            for p in data['readers']:
                if not p['done']:
                    mentions += f"[{p['name']}](tg://user?id={p['id']}) "
            
            if mentions:
                # تم استبدال النجوم بـ 🌿
                msg = f"🔔 هَلُمُّوا إِلَى مَجْلِسٍ تَحُفُّنَا فِيهِ المَلَائِكَةُ 🌿\n\nننتظر إتمامكن للورد القراءاتي:\n{mentions}"
                bot.send_message(cid, msg, parse_mode="Markdown")
            else:
                bot.answer_callback_query(call.id, "ما شاء الله، الجميع أتم!")

    elif call.data == "toggle_lock":
        if is_user_admin(cid, uid): data['is_open'] = not data['is_open']

    elif call.data == "toggle_extra":
        if is_user_admin(cid, uid): data['extra_allowed'] = not data['extra_allowed']

    elif call.data == "admin_report":
        if is_user_admin(cid, uid):
            done = [p['name'] for p in data['readers'] if p['done']]
            rep = "🏆 **تَقْرِيرُ مَجْلِسِ اليَوْم** 🏆\n\nنِسَاءٌ مُبَارَكَاتٌ أَتْمَمْنَ القِرَاءَةَ:\n" + ("\n".join(done) if done else "لا يوجد بعد")
            bot.send_message(cid, rep)

    elif call.data == "admin_del_panel":
        if is_user_admin(cid, uid):
            del_m = types.InlineKeyboardMarkup()
            for p in data['readers']:
                del_m.add(types.InlineKeyboardButton(f"🗑️ {p['name']}", callback_data=f"del_{p['id']}"))
            for p in data['listeners']:
                del_m.add(types.InlineKeyboardButton(f"🎧 {p['name']}", callback_data=f"del_{p['id']}"))
            del_m.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="back"))
            bot.edit_message_text("لوحة حذف الأسماء (للمشرفات):", cid, call.message.message_id, reply_markup=del_m)
            return

    elif call.data.startswith("del_"):
        if is_user_admin(cid, uid):
            target_id = int(call.data.split("_")[1])
            data['readers'] = [p for p in data['readers'] if p['id'] != target_id]
            data['listeners'] = [p for p in data['listeners'] if p['id'] != target_id]
            bot.answer_callback_query(call.id, "تم الحذف بنجاح.")

    bot.edit_message_text(build_report_text(), cid, call.message.message_id, reply_markup=generate_main_markup(cid, uid))

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()
