import telebot
from telebot import types
import random
import os
import threading

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN environment variable is not set.")

SECRET_KEY = "X7Q9M2L8ZT4R5VK8N3Q"

bot = telebot.TeleBot(TOKEN)

# ------------------- NUMBER POOLS -------------------
HIGH_CHANCE_NUMBERS = [
    "+91 9527688772", "+91 6357526321", "+91 8255794930", "+91 9541095798",
    "+91 9502408847", "+91 6362572588", "+91 9513874091", "+91 7532683201",
    "+91 7061477936", "+91 7071543265", "+91 7008715222", "+91 7093784783",
    "+91 8222957542", "+91 7586981554", "+91 8270321562", "+91 8267610270",
    "+91 6381177425", "+91 6305905396", "+91 6351535148", "+91 7009454796"
]

MEDIUM_CHANCE_NUMBERS = [
    "+91 7592913190", "+91 7530519859", "+91 9554021340", "+91 7001568364",
    "+91 7063139816", "+91 8298746304", "+91 6304384427", "+91 7572194354",
    "+91 9575188128", "+91 7023761991", "+91 6336668371", "+91 8207775856",
    "+91 6371839914", "+91 8268731005", "+91 6385890643", "+91 7551873652",
    "+91 7054962699", "+91 8242788830", "+91 6327405525", "+91 6361482463"
]

LOW_CHANCE_NUMBERS = [
    "+91 8201185045", "+91 6370141125", "+91 6324650428", "+91 7016953641",
    "+91 6388463289", "+91 7027199637", "+91 6396470195", "+91 7050539651",
    "+91 7048826119", "+91 6330875861", "+91 7517509538", "+91 8200731133",
    "+91 7516567501", "+91 6332027133", "+91 6308009523", "+91 7077982744",
    "+91 7040464670", "+91 9578422701", "+91 8209920787", "+91 8263528575"
]

# ------------------- User data -------------------
user_data = {}

# ------------------- Generate random OTP -------------------
def generate_otp():
    digits = str(random.randint(100000, 999999))
    return f"{digits[:3]}-{digits[3:]}"

# ------------------- Send OTP after 60 seconds -------------------
def send_otp_after_delay(user_id, pasted_number):
    otp = generate_otp()
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(
            f"📋 Copy OTP: {otp}",
            copy_text=types.CopyTextButton(text=otp)
        )
    )
    bot.send_message(
        user_id,
        f"📩 *SMS Received!*\n\n"
        f"📞 Number: `{pasted_number}`\n"
        f"🔢 *OTP:* `{otp}`\n\n"
        f"⏱️ Valid for 10 minutes.",
        parse_mode="Markdown",
        reply_markup=markup
    )

# ------------------- Main Menu Keyboard -------------------
def main_menu_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📞 Get Number")
    return markup

# ------------------- /start -------------------
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    user_data[user_id] = {}
    bot.send_message(
        user_id,
        "👋 Welcome! 🎁 Free Numbers Available\n\n"
        "Press the button below to get a number.",
        reply_markup=main_menu_keyboard()
    )

# ------------------- Get Number -------------------
@bot.message_handler(func=lambda m: m.text == "📞 Get Number")
def get_number_start(message):
    user_id = message.chat.id
    user_data[user_id] = {}

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🇮🇳 India", callback_data="country_India"),
        types.InlineKeyboardButton("🇳🇵 Nepal", callback_data="country_Nepal"),
        types.InlineKeyboardButton("🇵🇰 Pakistan", callback_data="country_Pakistan")
    )
    bot.send_message(user_id, "🌍 Select your country:", reply_markup=markup)

# ------------------- Callback: Country selected -------------------
@bot.callback_query_handler(func=lambda call: call.data.startswith("country_"))
def country_selected(call):
    user_id = call.message.chat.id
    country = call.data.split("_")[1]
    user_data[user_id]["country"] = country

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📱 WhatsApp", callback_data="service_WhatsApp"),
        types.InlineKeyboardButton("📘 Facebook", callback_data="service_Facebook"),
        types.InlineKeyboardButton("📞 Telegram", callback_data="service_Telegram"),
        types.InlineKeyboardButton("🔧 Others", callback_data="service_Others")
    )
    bot.edit_message_text(
        f"✅ Country: {country}\n\n📱 Choose your service:",
        user_id, call.message.message_id, reply_markup=markup
    )

# ------------------- Callback: Service selected -------------------
@bot.callback_query_handler(func=lambda call: call.data.startswith("service_"))
def service_selected(call):
    user_id = call.message.chat.id
    service = call.data.split("_")[1]
    user_data[user_id]["service"] = service
    user_data[user_id]["awaiting_key"] = True

    bot.edit_message_text(
        f"✅ Country: {user_data[user_id]['country']}\n"
        f"📱 Service: {service}",
        user_id, call.message.message_id
    )
    bot.send_message(
        user_id,
        "🔑 Enter your key below:\n\n"
        "⚠️ Without the correct key, numbers will not be shown.",
        reply_markup=types.ForceReply(selective=True, input_field_placeholder="Enter key here...")
    )

# ------------------- Handle Key Input -------------------
@bot.message_handler(func=lambda m: user_data.get(m.chat.id, {}).get("awaiting_key", False))
def verify_key(message):
    user_id = message.chat.id
    key_entered = message.text.strip()

    # Delete the message immediately so the key disappears from chat
    try:
        bot.delete_message(user_id, message.message_id)
    except Exception:
        pass

    if key_entered == SECRET_KEY:
        user_data[user_id]["key_verified"] = True
        user_data[user_id]["awaiting_key"] = False
        bot.send_message(user_id, "✅ Key verified!")
        show_numbers(user_id)
    else:
        bot.send_message(
            user_id,
            "❌ Wrong key!\n\n"
            "Please enter the correct key.\n\n"
            "⚠️ Without the correct key, numbers will not be shown."
        )

# ------------------- Show Numbers -------------------
def show_numbers(user_id):
    country = user_data[user_id].get("country", "India")
    service = user_data[user_id].get("service", "WhatsApp")

    high_num = random.choice(HIGH_CHANCE_NUMBERS)
    medium_num = random.choice(MEDIUM_CHANCE_NUMBERS)
    low_num = random.choice(LOW_CHANCE_NUMBERS)

    high_num_clean = high_num.replace(" ", "")
    medium_num_clean = medium_num.replace(" ", "")
    low_num_clean = low_num.replace(" ", "")

    user_data[user_id]["numbers"] = {
        "high": high_num_clean,
        "medium": medium_num_clean,
        "low": low_num_clean
    }
    user_data[user_id]["awaiting_number_paste"] = True

    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton(
            f"🟢 {high_num_clean} (High Chance) — Tap to Copy",
            copy_text=types.CopyTextButton(text=high_num_clean)
        ),
        types.InlineKeyboardButton(
            f"🟡 {medium_num_clean} (Medium Chance) — Tap to Copy",
            copy_text=types.CopyTextButton(text=medium_num_clean)
        ),
        types.InlineKeyboardButton(
            f"🔴 {low_num_clean} (Low Chance) — Tap to Copy",
            copy_text=types.CopyTextButton(text=low_num_clean)
        ),
        types.InlineKeyboardButton("🔄 Get New Numbers", callback_data="new_numbers")
    )

    text = (
        f"✅ Country: {country}\n"
        f"📱 Service: {service}\n\n"
        f"📞 **These numbers are ready to receive SMS:**\n\n"
        f"🟢 **High Chance** - Most likely to receive OTP\n"
        f"🟡 **Medium Chance** - May receive OTP\n"
        f"🔴 **Low Chance** - Less likely to receive OTP\n\n"
        f"👇 **Tap any number to copy it**"
    )

    bot.send_message(user_id, text, parse_mode="Markdown", reply_markup=markup)
    bot.send_message(
        user_id,
        "📋 Copy and paste any number to receive OTP.",
        reply_markup=main_menu_keyboard()
    )

# ------------------- Handle Pasted Number (OTP trigger) -------------------
@bot.message_handler(func=lambda m: (
    m.text and
    m.text != "📞 Get Number" and
    not m.text.startswith("/") and
    user_data.get(m.chat.id, {}).get("awaiting_number_paste", False)
))
def handle_pasted_number(message):
    user_id = message.chat.id
    pasted_number = message.text.strip()

    bot.send_message(
        user_id,
        f"✅ Number received: `{pasted_number}`\n\n"
        f"⏳ We are waiting for OTP...",
        parse_mode="Markdown"
    )

    timer = threading.Timer(60.0, send_otp_after_delay, args=[user_id, pasted_number])
    timer.daemon = True
    timer.start()

# ------------------- Callback: Get New Numbers -------------------
@bot.callback_query_handler(func=lambda call: call.data == "new_numbers")
def new_numbers_callback(call):
    user_id = call.message.chat.id
    if user_id in user_data and user_data[user_id].get("key_verified", False):
        bot.edit_message_text("🔄 Generating new numbers...", user_id, call.message.message_id)
        show_numbers(user_id)
    else:
        bot.answer_callback_query(call.id, "❌ Please verify your key first!")

# ------------------- Fallback -------------------
@bot.message_handler(func=lambda m: True)
def fallback(message):
    bot.send_message(
        message.chat.id,
        "⚠️ Please use the button below or /start",
        reply_markup=main_menu_keyboard()
    )

# ------------------- Run -------------------
print("🤖 Bot is running...")
print(f"📊 Loaded {len(HIGH_CHANCE_NUMBERS)} high, {len(MEDIUM_CHANCE_NUMBERS)} medium, {len(LOW_CHANCE_NUMBERS)} low chance numbers")
bot.infinity_polling(skip_pending=True)
