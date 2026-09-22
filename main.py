import os
import secrets
import string
import logging
from telebot import TeleBot, types

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load token from environment variable
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set")

bot = TeleBot(BOT_TOKEN)

# Character pools
LOWERCASE = string.ascii_lowercase
UPPERCASE = string.ascii_uppercase
DIGITS = string.digits
SYMBOLS = "!@#$%^&*()-_=+[]{};:,.?"

def generate_password(length=16, use_symbols=True):
    """Generate a cryptographically secure password."""
    pool = LOWERCASE + UPPERCASE + DIGITS
    if use_symbols:
        pool += SYMBOLS
    
    # Ensure at least one character from each required category
    password = [
        secrets.choice(LOWERCASE),
        secrets.choice(UPPERCASE),
        secrets.choice(DIGITS),
    ]
    if use_symbols:
        password.append(secrets.choice(SYMBOLS))
    
    # Fill the rest with random choices from the full pool
    for _ in range(length - len(password)):
        password.append(secrets.choice(pool))
    
    # Shuffle to avoid predictable positions
    secrets.SystemRandom().shuffle(password)
    return "".join(password)

def get_generate_keyboard():
    """Create inline keyboard for generating passwords."""
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_generate = types.InlineKeyboardButton("🔐 Generate Password", callback_data="generate")
    btn_symbols = types.InlineKeyboardButton("⚙️ Symbols: ON", callback_data="toggle_symbols")
    markup.add(btn_generate)
    markup.add(btn_symbols)
    return markup

# Track user preference (symbols on/off)
user_prefs = {}

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """Handle /start and /help commands."""
    user_id = message.from_user.id
    if user_id not in user_prefs:
        user_prefs[user_id] = {"symbols": True}
    
    welcome_text = (
        "🔐 *Password Generator*\n\n"
        "I create strong, random passwords locally using cryptographically secure methods.\n\n"
        "• Passwords are generated on this server\n"
        "• Never stored or transmitted elsewhere\n"
        "• Use the button below to generate\n\n"
        "Click to generate a secure password:"
    )
    bot.send_message(
        message.chat.id,
        welcome_text,
        parse_mode="Markdown",
        reply_markup=get_generate_keyboard()
    )

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    """Handle inline button presses."""
    user_id = call.from_user.id
    if user_id not in user_prefs:
        user_prefs[user_id] = {"symbols": True}
    
    if call.data == "generate":
        use_symbols = user_prefs[user_id]["symbols"]
        password = generate_password(length=16, use_symbols=use_symbols)
        
        # Send the generated password
        response = f"🔑 *Your Password:*\n\n`{password}`\n\n_Click to copy. Generate a new one anytime._"
        bot.send_message(
            call.message.chat.id,
            response,
            parse_mode="Markdown",
            reply_markup=get_generate_keyboard()
        )
        bot.answer_callback_query(call.id, "New password generated ✓")
    
    elif call.data == "toggle_symbols":
        current = user_prefs[user_id]["symbols"]
        user_prefs[user_id]["symbols"] = not current
        new_state = "ON" if not current else "OFF"
        
        # Update the keyboard label
        markup = types.InlineKeyboardMarkup(row_width=2)
        btn_generate = types.InlineKeyboardButton("🔐 Generate Password", callback_data="generate")
        btn_symbols = types.InlineKeyboardButton(f"⚙️ Symbols: {new_state}", callback_data="toggle_symbols")
        markup.add(btn_generate)
        markup.add(btn_symbols)
        
        bot.edit_message_reply_markup(
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
        bot.answer_callback_query(call.id, f"Symbols turned {new_state}")

@bot.message_handler(func=lambda message: True)
def fallback(message):
    """Handle any other messages."""
    bot.reply_to(
        message,
        "Use /start to generate a password.",
        reply_markup=get_generate_keyboard()
    )

if __name__ == "__main__":
    logger.info("Starting Password Generator Bot...")
    bot.infinity_polling(timeout=30, long_polling_timeout=30)
