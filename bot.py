import telebot
from telebot import types
import time
from datetime import datetime
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "Bot is Online!"

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run).start()

TOKEN = '8684986706:AAF6pkJQ8a4N3XeecnnJOXhsJpr8z7gv8bs'
bot = telebot.TeleBot(TOKEN)

data = {
    'readers': [], 'listeners': [], 'extra': [], 
    'surah': "لم تحدد بعد"
}

def esc(text):
    for c in ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']:
        text = text.replace(c, f"\\{c}")
    return text

def build_menu(uid, cid):
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(types.InlineKeyboardButton("📝 سجل اسمي", callback_data="reg_r"),
          types.InlineKeyboardButton("❌ احذف اسمي", callback_data="del"))
    m.add(types.InlineKeyboardButton("✅ قرأت", callback_data="done"),
          types.InlineKeyboardButton("🎧 مستمعة", callback_data="reg_l"))
    m.add(types.InlineKeyboardButton("🌸 معتذرة (إضافي)", callback_data="reg_e"))
    m.add(types.InlineKeyboardButton("🔄 تحديث القائمة", callback_data="refresh"))
    
    # التحقق من المشرفات لإظهار زر الإعدادات
    try:
        status = bot.get_chat_member(cid, uid).status
        if status in ['administrator', 'creator'] or cid > 0:
            m.add(types.InlineKeyboardButton("⚙️ إعدادات المشرفات", callback_data="admin"))
    except: pass
    return m

def get_text():
    day = datetime.now().strftime("%d/%m/%Y")
    t = f"❄️ *بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ* ❄️\n🌿 *مَجْلِسُ تِلَاوَةِ القُرْآنِ الكَرِيمِ* 🌿\n\n"
    t += f"🗓️ {esc(day)} م\n"
    t += f"📍 *السُّورَةُ:* {esc(data['surah'])}\n"
    t += "━━━━━━━━━━━━━━\n\n"
    
    t += "📖 *القارئات:*\n"
    if not data['readers']: t += "⏳ في انتظار التسجيل\\.\\.\n"
    else:
        for i, p in enumerate(data['readers'], 1):
            s = "✅" if p['done'] else "⏳"
            t += f"{i}\\- [{esc(p['name'])}](tg://user?id={p['id']}) {s}\n"
            
    t += "\n✨ *الأدوار الإضافية:*\n"
    for i, p in enumerate(data['extra'], 1):
        t += f"{i}\\- [{esc(p['name'])}](tg://user?id={p['id']}) ⭐\n"

    t += "\n🎧 *المستمعات:*\n"
    for i, p in enumerate(data['listeners'], 1):
        t += f"{i}\\- [{esc(p['name'])}](tg://user?id={p['id']}) 🌿\n"
    
    t += "\n━━━━━━━━━━━━━━\n"
    t += "اللهم اجعلنا ممن يقال لهم:\n*(اقرأ وارتقِ ورتل كما كنت ترتل في الدنيا)*"
    return t

@bot.callback_query_handler(func=lambda call: True)
def handle(call):
    uid, uname, cid = call.from_user.id, call.from_user.first_name, call.message.chat.id
    
    if call.data == "reg_r":
        if not any(p['id'] == uid for p in data['readers']):
            data['readers'].append({'id': uid, 'name': uname, 'done': False})
    elif call.data == "reg_l":
        if not any(p['id'] == uid for p in data['listeners']):
            data['listeners'].append({'id': uid, 'name': uname})
    elif call.data == "reg_e":
        if not any(p['id'] == uid for p in data['extra']):
            data['extra'].append({'id': uid, 'name': uname})
    elif call.data == "done":
        for p in data['readers']:
            if p['id'] == uid: p['done'] = True
    elif call.data == "del":
        data['readers'] = [p for p in data['readers'] if p['id'] != uid]
        data['listeners'] = [p for p in data['listeners'] if p['id'] != uid]
        data['extra'] = [p for p in data['extra'] if p['id'] != uid]
    elif call.data == "admin":
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("✍️ تغيير السورة", callback_data="set_s"),
              types.InlineKeyboardButton("🧨 تصفير", callback_data="reset"))
        m.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="refresh"))
        return bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=m)
    elif call.data == "reset":
        data['readers'], data['listeners'], data['extra'] = [], [], []
    elif call.data == "set_s":
        return bot.send_message(cid, "اكتبي اسم السورة الجديدة:")

    try:
        bot.edit_message_text(get_text(), cid, call.message.message_id, parse_mode="MarkdownV2", reply_markup=build_menu(uid, cid), disable_web_page_preview=True)
    except: pass

@bot.message_handler(func=lambda m: True)
def messages(m):
    if m.text.startswith('/start'):
        bot.send_message(m.chat.id, get_text(), parse_mode="MarkdownV2", reply_markup=build_menu(m.from_user.id, m.chat.id), disable_web_page_preview=True)
    elif not m.text.startswith('/'): # لتغيير السورة ببساطة
        data['surah'] = m.text
        bot.reply_to(m, "✅ تم تحديث السورة")

if __name__ == "__main__":
    keep_alive()
    bot.remove_webhook()
    bot.infinity_polling(skip_pending=True)
