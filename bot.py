import telebot
from telebot import types
from datetime import datetime
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "Bot is Green Now!"

def run(): app.run(host='0.0.0.0', port=8080)
Thread(target=run).start()

TOKEN = '8684986706:AAF6pkJQ8a4N3XeecnnJOXhsJpr8z7gv8bs'
bot = telebot.TeleBot(TOKEN)

# البيانات
data = {'readers': [], 'listeners': [], 'extra': [], 'surah': "لم تحدد"}

def get_menu():
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(types.InlineKeyboardButton("📝 سجل اسمي", callback_data="r"),
          types.InlineKeyboardButton("❌ احذفني", callback_data="d"))
    m.add(types.InlineKeyboardButton("✅ قرأت", callback_data="done"),
          types.InlineKeyboardButton("🎧 مستمعة", callback_data="l"))
    m.add(types.InlineKeyboardButton("🌸 إضافي", callback_data="e"),
          types.InlineKeyboardButton("🔄 تحديث", callback_data="ref"))
    return m

def get_text():
    d = datetime.now().strftime("%d/%m/%Y")
    t = f"❄️ *مَجْلِسُ تِلَاوَةِ القُرْآنِ* ❄️\n🗓️ {d}\n📍 *السُّورَةُ:* {data['surah']}\n\n"
    t += "📖 *القارئات:*\n"
    for i, p in enumerate(data['readers'], 1):
        t += f"{i}\\- [{p['n']}](tg://user?id={p['id']}) {'✅' if p['v'] else '⏳'}\n"
    t += "\n🎧 *المستمعات:*\n"
    for i, p in enumerate(data['listeners'], 1):
        t += f"{i}\\- [{p['n']}](tg://user?id={p['id']}) 🌿\n"
    t += "\n🌸 *إضافي:*\n"
    for i, p in enumerate(data['extra'], 1):
        t += f"{i}\\- [{p['n']}](tg://user?id={p['id']}) ⭐\n"
    return t

@bot.callback_query_handler(func=lambda c: True)
def calls(c):
    u, n, cid = c.from_user.id, c.from_user.first_name, c.message.chat.id
    if c.data == "r" and not any(p['id']==u for p in data['readers']): data['readers'].append({'id':u, 'n':n, 'v':False})
    elif c.data == "l" and not any(p['id']==u for p in data['listeners']): data['listeners'].append({'id':u, 'n':n})
    elif c.data == "e" and not any(p['id']==u for p in data['extra']): data['extra'].append({'id':u, 'n':n})
    elif c.data == "done":
        for p in data['readers']:
            if p['id'] == u: p['v'] = True
    elif c.data == "d":
        data['readers'] = [p for p in data['readers'] if p['id'] != u]
        data['listeners'] = [p for p in data['listeners'] if p['id'] != u]
        data['extra'] = [p for p in data['extra'] if p['id'] != u]
    
    try: bot.edit_message_text(get_text(), cid, c.message.message_id, parse_mode="MarkdownV2", reply_markup=get_menu())
    except: pass

@bot.message_handler(commands=['start'])
def st(m):
    bot.send_message(m.chat.id, get_text(), parse_mode="MarkdownV2", reply_markup=get_menu())

@bot.message_handler(func=lambda m: not m.text.startswith('/'))
def set_s(m):
    data['surah'] = m.text
    bot.reply_to(m, "✅ تم تغيير السورة")

bot.infinity_polling()
