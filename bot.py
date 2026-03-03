import telebot
from telebot import types
import time
from flask import Flask
from threading import Thread

# --- إعداد سيرفر وهمي لإبقاء البوت حياً ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
# ---------------------------------------

TOKEN = '8753124430:AAFrkVk2xu8FlIdZYhYKXziJxlHY_We3v7Q'
bot = telebot.TeleBot(TOKEN)

# ذاكرة البوت
data = {
    'readers': [], 
    'listeners': [], 
    'current_page': 0,
    'is_open': True
}

def is_user_admin(chat_id, user_id):
    """التحقق من رتبة المستخدم"""
    if chat_id > 0: return True
    try:
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ['administrator', 'creator']
    except:
        return False

def generate_main_markup(chat_id, user_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📝 سجل اسمي للقراءة", callback_data="reg_read"),
        types.InlineKeyboardButton("🎧 سجل اسمي كمستمعة", callback_data="reg_listen")
    )
    markup.add(
        types.InlineKeyboardButton("✅ أتممت القراءة", callback_data="set_done"),
        types.InlineKeyboardButton("🗑️ حذف اسم (للمشرفات)", callback_data="admin_del_panel")
    )
    
    if is_user_admin(chat_id, user_id):
        toggle_text = "🔓 فتح القائمة" if not data['is_open'] else "🔒 إغلاق القائمة"
        markup.add(types.InlineKeyboardButton(toggle_text, callback_data="toggle_lock"))
        
    return markup

def build_report_text():
    status_label = "🔓 مفتوحة" if data['is_open'] else "🔒 مغلقة"
    text = f"❄ بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ ❄\n"
    text += f"حالة القائمة: **{status_label}**\n\n"
    
    text += "📖 **المسجلات للقراءة:**\n"
    if not data['readers']:
        text += "لا يوجد مسجلات بعد..\n"
    else:
        for i, p in enumerate(data['readers'], 1):
            icon = "✅" if p['done'] else "⏳"
            text += f"{i}- {p['name']} (صـ {p['range']}) {icon}\n"
            
    text += "\n🎧 **المستمعات:**\n"
    if not data['listeners']:
        text += "لا يوجد مستمعات بعد..\n"
    else:
        for i, p in enumerate(data['listeners'], 1):
            text += f"{i}- {p['name']} ✨\n"
            
    text += f"\n📍 الصفحة التالية تبدأ من: {data['current_page']}"
    return text

@bot.message_handler(commands=['start'])
def start_bot(m):
    bot.send_message(m.chat.id, "البوت جاهز للعمل.", reply_markup=generate_main_markup(m.chat.id, m.from_user.id))

@bot.message_handler(func=lambda m: "بداية الوجه" in m.text)
def set_start_page(m):
    if is_user_admin(m.chat.id, m.from_user.id):
        nums = ''.join(filter(str.isdigit, m.text))
        if nums:
            data['current_page'] = int(nums)
            data['readers'], data['listeners'] = [], []
            data['is_open'] = True
            bot.send_message(m.chat.id, f"✅ تم الضبط صـ {nums}", reply_markup=generate_main_markup(m.chat.id, m.from_user.id))

@bot.callback_query_handler(func=lambda call: True)
def handle_buttons(call):
    uid, uname, cid = call.from_user.id, call.from_user.first_name, call.message.chat.id
    
    if call.data in ["reg_read", "reg_listen"] and not data['is_open']:
        bot.answer_callback_query(call.id, "⚠️ القائمة مغلقة حالياً.", show_alert=True)
        return

    if call.data == "reg_read":
        if any(p['id'] == uid for p in data['readers']): return
        start_p = data['current_page']
        end_p = start_p + 2
        data['readers'].append({'id': uid, 'name': uname, 'range': f"{start_p}-{end_p}", 'done': False})
        data['current_page'] = end_p + 1
        
    elif call.data == "reg_listen":
        if any(p['id'] == uid for p in data['listeners']): return
        data['listeners'].append({'id': uid, 'name': uname})
        
    elif call.data == "set_done":
        for p in data['readers']:
            if p['id'] == uid: p['done'] = True
            
    elif call.data == "toggle_lock":
        if is_user_admin(cid, uid):
            data['is_open'] = not data['is_open']
            
    elif call.data == "admin_del_panel":
        if is_user_admin(cid, uid):
            del_m = types.InlineKeyboardMarkup()
            for p in data['readers'] + data['listeners']:
                del_m.add(types.InlineKeyboardButton(f"🗑️ {p['name']}", callback_data=f"del_{p['id']}"))
            del_m.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="back"))
            bot.edit_message_text("اختاري الاسم للحذف:", cid, call.message.message_id, reply_markup=del_m)
            return

    elif call.data.startswith("del_"):
        if is_user_admin(cid, uid):
            target = int(call.data.split("_")[1])
            data['readers'] = [p for p in data['readers'] if p['id'] != target]
            data['listeners'] = [p for p in data['listeners'] if p['id'] != target]
    
    bot.edit_message_text(build_report_text(), cid, call.message.message_id, reply_markup=generate_main_markup(cid, uid))

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()
