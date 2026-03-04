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
    'start_page': 0,
    'is_open': True,
    'extra_allowed': False,
    'page_step': 2,
    'swap_temp': None 
}

def is_user_admin(chat_id, user_id):
    if chat_id > 0: return True 
    try:
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ['administrator', 'creator']
    except: return False

def reorder_pages():
    current = data['start_page']
    for p in data['readers']:
        start_p = current
        end_p = start_p + (data['page_step'] - 1)
        p['range'] = f"{start_p}-{end_p}"
        p['start_val'] = start_p
        current = end_p + 1

def generate_main_markup(chat_id, user_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("🔄 اختيار الحالة (قارئة/مستمعة)", callback_data="choose_status"))
    
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
        markup.add(
            types.InlineKeyboardButton("🔀 تبديل أدوار", callback_data="admin_swap_panel"),
            types.InlineKeyboardButton("🔃 تحديث القائمة", callback_data="admin_refresh")
        )
        
        lock_text = "🔓 فتح التسجيل" if not data['is_open'] else "🔒 إغلاق التسجيل"
        extra_text = "🚫 منع الإضافي" if data['extra_allowed'] else "🌿 تفعيل الإضافي"
        
        markup.add(types.InlineKeyboardButton(lock_text, callback_data="toggle_lock"),
                   types.InlineKeyboardButton(extra_text, callback_data="toggle_extra"))
        markup.add(types.InlineKeyboardButton("🧨 تصفير", callback_data="admin_reset"),
                   types.InlineKeyboardButton("⚙️ لوحة الحذف", callback_data="admin_del_panel"))
        
    return markup

def build_report_text():
    status = "✅ مفتوحة" if data['is_open'] else "❌ مغلقة"
    reorder_pages()
    text = f"❄ بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ ❄\n"
    text += f"🌿 **مَجْلِسُ تِلَاوَةِ القُرْآنِ الكَرِيمِ** 🌿\n"
    text += f"━━━━━━━━━━━━━\n"
    text += f"حالة القائمة: {status}\n"
    next_p = (data['readers'][-1]['start_val'] + data['page_step']) if data['readers'] else data['start_page']
    text += f"📍 الصفحة التالية: {next_p}\n"
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
    bot.send_message(m.chat.id, build_report_text(), reply_markup=generate_main_markup(m.chat.id, m.from_user.id))

@bot.message_handler(func=lambda m: "بداية الوجه" in m.text)
def set_start_page(m):
    if is_user_admin(m.chat.id, m.from_user.id):
        nums = ''.join(filter(str.isdigit, m.text))
        if nums:
            data['start_page'] = int(nums)
            bot.send_message(m.chat.id, f"✅ تم ضبط البداية من ص {nums}\nكم صفحة لكل طالبة؟")
            bot.register_next_step_handler(m, set_step)

def set_step(m):
    if m.text.isdigit():
        data['page_step'] = int(m.text)
        bot.send_message(m.chat.id, f"✅ تم الضبط: {m.text} صفحات.", reply_markup=generate_main_markup(m.chat.id, m.from_user.id))

@bot.callback_query_handler(func=lambda call: True)
def handle_buttons(call):
    uid, uname, cid = call.from_user.id, call.from_user.first_name, call.message.chat.id
    
    if call.data == "choose_status":
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("📖 تسجيل كقارئة", callback_data="reg_read"),
              types.InlineKeyboardButton("🎧 تسجيل كمستمعة", callback_data="reg_listen"))
        m.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="back_to_main"))
        bot.edit_message_text("اختاري حالتكِ في المجلس:", cid, call.message.message_id, reply_markup=m)
        return

    elif call.data == "reg_read":
        if any(p['id'] == uid for p in data['readers']): 
            bot.answer_callback_query(call.id, "أنتِ مسجلة كقارئة بالفعل!")
        else:
            data['readers'].append({'id': uid, 'name': uname, 'done': False})
            reorder_pages()
            bot.answer_callback_query(call.id, "تم تسجيلكِ كقارئة.")
        
    elif call.data == "reg_listen":
        if any(p['id'] == uid for p in data['listeners']):
            bot.answer_callback_query(call.id, "أنتِ مسجلة كمستمعة بالفعل!")
        else:
            data['listeners'].append({'id': uid, 'name': uname})
            bot.answer_callback_query(call.id, "تم تسجيلكِ كمستمعة.")

    elif call.data == "reg_extra":
        data['readers'].append({'id': uid, 'name': f"{uname} (إضافي)", 'done': False})
        reorder_pages()
        bot.answer_callback_query(call.id, "تم إضافة دور جديد.")

    elif call.data == "set_done":
        found = False
        for p in data['readers']:
            if p['id'] == uid:
                p['done'] = True
                found = True
        if found: 
            bot.answer_callback_query(call.id, "تَقَبَّلَ اللَّهُ طَاعَتَكِ ✅")
        else: 
            bot.answer_callback_query(call.id, "يجب التسجيل أولاً!", show_alert=True)

    elif call.data == "user_del":
        data['readers'] = [p for p in data['readers'] if p['id'] != uid]
        data['listeners'] = [p for p in data['listeners'] if p['id'] != uid]
        reorder_pages()
        bot.answer_callback_query(call.id, "تم حذف اسمكِ وتعديل الأوجه.")

    elif call.data == "admin_refresh":
        bot.delete_message(cid, call.message.message_id)
        bot.send_message(cid, build_report_text(), reply_markup=generate_main_markup(cid, uid))
        return

    elif call.data == "admin_reset":
        if is_user_admin(cid, uid):
            data['readers'], data['listeners'] = [], []
            bot.answer_callback_query(call.id, "تم تصفير القائمة 🧨")
        else: bot.answer_callback_query(call.id, "للمشرفات فقط!", show_alert=True)

    elif call.data == "admin_report":
        if is_user_admin(cid, uid):
            done = [p['name'] for p in data['readers'] if p['done']]
            rep = "🏆 **تَقْرِيرُ مَجْلِسِ اليَوْم** 🏆\n\nنِسَاءٌ مُبَارَكَاتٌ أَتْمَمْنَ القِرَاءَةَ:\n" + ("\n".join(done) if done else "لا يوجد بعد")
            bot.send_message(cid, rep)
            return

    elif call.data == "admin_remind":
        bot.send_message(cid, "🔔 هَلُمُّوا إِلَى مَجْلِسٍ تَحُفُّنَا فِيهِ المَلَائِكَةُ 🌿")

    elif call.data == "admin_swap_panel":
        if is_user_admin(cid, uid):
            m = types.InlineKeyboardMarkup()
            for i, p in enumerate(data['readers']):
                m.add(types.InlineKeyboardButton(f"🔄 {p['name']}", callback_data=f"sw1_{i}"))
            m.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="back_to_main"))
            bot.edit_message_text("اختاري الطالبة الأولى للتبديل:", cid, call.message.message_id, reply_markup=m)
            return

    elif call.data.startswith("sw1_"):
        idx1 = int(call.data.split("_")[1])
        data['swap_temp'] = idx1
        m = types.InlineKeyboardMarkup()
        for i, p in enumerate(data['readers']):
            if i != idx1:
                m.add(types.InlineKeyboardButton(f"🤝 مع {p['name']}", callback_data=f"sw2_{i}"))
        bot.edit_message_text(f"تبديل {data['readers'][idx1]['name']} مع من؟", cid, call.message.message_id, reply_markup=m)
        return

    elif call.data.startswith("sw2_"):
        idx2 = int(call.data.split("_")[1])
        idx1 = data['swap_temp']
        data['readers'][idx1], data['readers'][idx2] = data['readers'][idx2], data['readers'][idx1]
        reorder_pages()
        data['swap_temp'] = None
        bot.answer_callback_query(call.id, "تم التبديل وتعديل الأوجه ✅")

    elif call.data == "admin_del_panel":
        if is_user_admin(cid, uid):
            del_m = types.InlineKeyboardMarkup()
            for p in data['readers']:
                del_m.add(types.InlineKeyboardButton(f"🗑️ {p['name']}", callback_data=f"del_{p['id']}"))
            del_m.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="back_to_main"))
            bot.edit_message_text("لوحة الحذف:", cid, call.message.message_id, reply_markup=del_m)
            return

    elif call.data.startswith("del_"):
        target_id = int(call.data.split("_")[1])
        data['readers'] = [p for p in data['readers'] if p['id'] != target_id]
        reorder_pages()
        bot.answer_callback_query(call.id, "تم الحذف وتعديل الأوجه.")

    elif call.data == "toggle_lock":
        if is_user_admin(cid, uid): data['is_open'] = not data['is_open']

    elif call.data == "toggle_extra":
        if is_user_admin(cid, uid): data['extra_allowed'] = not data['extra_allowed']

    elif call.data == "back_to_main":
        pass

    # تحديث الرسالة الرئيسية بعد أي حركة
    try:
        bot.edit_message_text(build_report_text(), cid, call.message.message_id, reply_markup=generate_main_markup(cid, uid))
    except: pass

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()
