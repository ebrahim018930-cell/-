import sqlite3
import telebot
from telebot import types

# আপনার বটের টোকেন এবং অ্যাডমিন আইডি
TOKEN = "8846876957:AAEwkCa-szVplHOABURWQ_RIUAb_4TikMII"
ADMIN_ID = 6565134353  

bot = telebot.TeleBot(TOKEN)

# ডেটাবেস সংযোগ ও টেবিল তৈরি
def init_db():
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    # ইউজার টেবিল
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance REAL DEFAULT 0.0,
            referrals INTEGER DEFAULT 0
        )
    ''')
    # ডায়নামিক সেটংস টেবিল (রেফার বোনাস ইত্যাদির জন্য)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value REAL
        )
    ''')
    # ডিফল্ট রেফার বোনাস ৫ টাকা সেট করা
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('refer_bonus', 5.0)")
    conn.commit()
    conn.close()

init_db()

def get_refer_bonus():
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = 'refer_bonus'")
    data = cursor.fetchone()
    conn.close()
    return data[0] if data else 5.0

def set_refer_bonus(amount):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE settings SET value = ? WHERE key = 'refer_bonus'", (amount,))
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT balance, referrals FROM users WHERE user_id = ?", (user_id,))
    data = cursor.fetchone()
    conn.close()
    return data

def add_user(user_id):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, balance, referrals) VALUES (?, 0.0, 0)", (user_id,))
    conn.commit()
    conn.close()

def add_referral_bonus(referrer_id, bonus):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = balance + ?, referrals = referrals + 1 WHERE user_id = ?", (bonus, referrer_id))
    conn.commit()
    conn.close()

def update_balance(user_id, amount):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

# অ্যাডমিন কাস্টম কমান্ড: রেফার বোনাস পরিবর্তন করা (যেমন: /setrefer 10)
@bot.message_handler(commands=['setrefer'])
def set_referral_command(message):
    if message.from_user.id == ADMIN_ID:
        try:
            args = message.text.split()
            if len(args) > 1:
                new_bonus = float(args[1])
                set_refer_bonus(new_bonus)
                bot.reply_to(message, f"✅ রেফারেল বোনাস সফলভাবে পরিবর্তন করা হয়েছে। নতুন বোনাস: ৳{new_bonus}")
            else:
                bot.reply_to(message, "❌ ব্যবহার নিয়ম: `/setrefer 10` (যে পরিমাণ দিতে চান)", parse_mode="Markdown")
        except ValueError:
            bot.reply_to(message, "❌ দয়া করে একটি সঠিক সংখ্যা লিখুন। (যেমন: `/setrefer 10`)", parse_mode="Markdown")
    else:
        bot.reply_to(message, "❌ আপনি এই কমান্ডটি ব্যবহার করার অধিকার রাখেন না।")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    user_data = get_user(user_id)
    current_bonus = get_refer_bonus()
    
    if not user_data:
        add_user(user_id)
        args = message.text.split()
        if len(args) > 1:
            try:
                referrer_id = int(args[1])
                if referrer_id != user_id and get_user(referrer_id):
                    add_referral_bonus(referrer_id, current_bonus)
                    bot.send_message(referrer_id, f"🎉 অভিনন্দন! আপনার রেফারেল লিংকে একজন জয়েন করায় ৳{current_bonus} যোগ হয়েছে।")
            except ValueError:
                pass

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("💰 ব্যালেন্স"), types.KeyboardButton("🔗 রেফারেল লিংক"))
    markup.add(types.KeyboardButton("💸 উইথড্র (বিকাশ/নগদ)"), types.KeyboardButton("💬 সাপোর্ট"))
    
    bot.send_message(message.chat.id, "স্বাগতম! নিচের অপশন থেকে নির্বাচন করুন:", reply_markup=markup)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    user_data = get_user(user_id)
    
    if not user_data:
        add_user(user_id)
        user_data = (0.0, 0)

    if message.text == "💰 ব্যালেন্স":
        balance, refs = user_data
        bot.reply_to(message, f"📊 **আপনার অ্যাকাউন্ট তথ্য:**\n\nবর্তমান ব্যালেন্স: ৳{balance}\nমোট রেফার: {refs} জন", parse_mode="Markdown")

    elif message.text == "🔗 রেফারেল লিংক":
        bot_username = bot.get_me().username
        current_bonus = get_refer_bonus()
        ref_link = f"https://t.me/{bot_username}?start={user_id}"
        bot.reply_to(message, f"🔗 **আপনার ব্যক্তিগত রেফারেল লিংক:**\n{ref_link}\n\nপ্রতিটি সফল রেফারে পাবেন ৳{current_bonus}!")

    elif message.text == "💸 উইথড্র (বিকাশ/নগদ)":
        balance = user_data[0]
        if balance < 50.0:  # মিনিমাম ৫০ টাকা উইথড্র
            bot.reply_to(message, "❌ উইথড্র করতে ন্যূনতম ৳৫০ ব্যালেন্স থাকতে হবে।")
        else:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("বিকাশ", callback_data="w_bkash"),
                       types.InlineKeyboardButton("নগদ", callback_data="w_nagad"))
            bot.reply_to(message, "টাকা নেওয়ার মাধ্যম সিলেক্ট করুন:", reply_markup=markup)

    elif message.text == "💬 সাপোর্ট":
        msg = bot.reply_to(message, "আপনার কোনো প্রশ্ন বা সমস্যা থাকলে নিচে বিস্তারিত লিখে মেসেজ পাঠান:")
        bot.register_next_step_handler(msg, send_support_message)

def send_support_message(message):
    user_id = message.from_user.id
    user_text = message.text
    
    # অ্যাডমিন আইডিতে সাপোর্ট বার্তা পাঠানো
    admin_support_text = f"📩 **নতুন সাপোর্ট মেসেজ!**\n\n**ইউজার ID:** `{user_id}`\n**নাম:** {message.from_user.first_name}\n**মেসেজ:** {user_text}"
    bot.send_message(ADMIN_ID, admin_support_text, parse_mode="Markdown")
    
    bot.reply_to(message, "✅ আপনার বার্তাটি অ্যাডমিনের কাছে সফলভাবে পাঠানো হয়েছে। খুব শীঘ্রই আপনার সাথে যোগাযোগ করা হবে।")

@bot.callback_query_handler(func=lambda call: call.data.startswith('w_'))
def process_withdraw(call):
    method = "বিকাশ (bKash)" if call.data == "w_bkash" else "নগদ (Nagad)"
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, f"আপনার {method} নম্বরটি লিখুন:")
    bot.register_next_step_handler(msg, save_withdrawal_number, method)

def save_withdrawal_number(message, method):
    user_id = message.from_user.id
    number = message.text
    user_data = get_user(user_id)
    balance = user_data[0]
    
    # অ্যাডমিনকে নোটিফিকেশন পাঠানো
    admin_text = f"🔔 **নতুন উইথড্র রিকোয়েস্ট!**\n\nইউজার ID: `{user_id}`\nমাধ্যম: {method}\nনম্বর: `{number}`\nপরিমাণ: ৳{balance}"
    bot.send_message(ADMIN_ID, admin_text, parse_mode="Markdown")
    
    # ব্যালেন্স ০ করা
    update_balance(user_id, 0.0)
    bot.reply_to(message, "✅ আপনার উইথড্র আবেদনটি গ্রহণ করা হয়েছে। অ্যাডমিন পর্যালোচনা করে শীঘ্রই পেমেন্ট পাঠিয়ে দেবে।")

print("Bot is working successfully...")
bot.infinity_polling()
