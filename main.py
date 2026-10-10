import telebot
from telebot import types

# ----------------- CONFIGURATION -----------------
API_TOKEN = '8846876957:AAEwkCa-szVplHOABURWQ_RIUAb_4TikMII'
ADMIN_ID = 6565134353

bot = telebot.TeleBot(API_TOKEN)

# System Data Storage
users = {}  # user_id: {'balance': 0.0, 'ref_by': None, 'referrals': 0, 'name': ''}
settings = {
    'referral_bonus': 5.0,
    'min_withdraw': 50.0,
    'channels': []  # List of required channels/groups
}

# Helper: Check Channel Membership
def is_subscribed(user_id):
    if not settings['channels']:
        return True
    for ch in settings['channels']:
        try:
            member = bot.get_chat_member(ch, user_id)
            if member.status in ['left', 'kicked']:
                return False
        except Exception:
            pass
    return True

# ----------------- USER HANDLERS -----------------

@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name or "User"
    args = message.text.split()

    if user_id not in users:
        ref_by = None
        if len(args) > 1 and args[1].isdigit():
            referrer = int(args[1])
            if referrer != user_id and referrer in users:
                ref_by = referrer

        users[user_id] = {
            'balance': 0.0,
            'ref_by': ref_by,
            'referrals': 0,
            'name': first_name
        }

        if ref_by:
            users[ref_by]['balance'] += settings['referral_bonus']
            users[ref_by]['referrals'] += 1
            try:
                bot.send_message(ref_by, f"🎉 **নতুন রেফারেল!**\nআপনি পেয়েছেন `{settings['referral_bonus']}` টাকা।", parse_mode="Markdown")
            except Exception:
                pass
    else:
        users[user_id]['name'] = first_name

    if not is_subscribed(user_id):
        markup = types.InlineKeyboardMarkup(row_width=1)
        for ch in settings['channels']:
            clean_username = ch.replace('@', '')
            markup.add(types.InlineKeyboardButton(f"📢 Join {ch}", url=f"https://t.me/{clean_username}"))
        markup.add(types.InlineKeyboardButton("🔄 Check Joined", callback_data="check_join"))
        
        bot.send_message(user_id, "⚠️ **বটটি ব্যবহার করতে নিচের সব চ্যানেল/গ্রুপে জয়েন করুন:**", reply_markup=markup, parse_mode="Markdown")
        return

    send_main_menu(user_id)

def send_main_menu(user_id):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add('💰 Balance', '🔗 Referral',
