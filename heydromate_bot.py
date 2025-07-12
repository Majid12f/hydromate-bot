import json
import asyncio
from datetime import datetime
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    filters
)

# ------------------- تنظیمات -------------------
TOKEN = "7541884480:AAEnbBsrYVQPfdPicYV9szJLqo43ajB-oic"
CHANNEL_ID = -1002703710685
CHANNEL_USERNAME = "@heroinroutine"
MAIN_ADMIN_ID = 206362948  # آی‌دی عددی خودت

DATA_FILE = "data.json"
ADMINS_FILE = "admins.json"

# ------------------- دیتابیس -------------------
def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def load_admins():
    try:
        with open(ADMINS_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_admins(admins):
    with open(ADMINS_FILE, "w") as f:
        json.dump(admins, f)

# ------------------- چک عضویت -------------------
async def check_user_in_channel(user_id, bot):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

# ------------------- دکمه‌ها -------------------
btn_drink = InlineKeyboardButton("💧 Drink", callback_data="drink")
btn_bottle = InlineKeyboardButton("📊 Bottle", callback_data="bottle")
btn_addadmin = InlineKeyboardButton("➕ Add Admin", callback_data="addadmin")
btn_removeadmin = InlineKeyboardButton("➖ Remove Admin", callback_data="removeadmin")
btn_showusers = InlineKeyboardButton("📋 Show Users", callback_data="show_users")
btn_showadmins = InlineKeyboardButton("👥 Show Admins", callback_data="show_admins")

keyboard_admin_panel = InlineKeyboardMarkup([
    [btn_drink],
    [btn_bottle],
    [btn_addadmin],
    [btn_removeadmin],
    [btn_showusers],
    [btn_showadmins]
])

join_keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("🔗 Channel", url=f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}"),
     InlineKeyboardButton("✅ I Joined", callback_data="check_join")]
])

# ------------------- طراحی بطری -------------------
def generate_bottle_text(glasses, goal):
    total_rows = goal
    filled = min(glasses, total_rows)
    extra = max(0, glasses - total_rows)
    empty = max(0, total_rows - filled)

    top = "   ______"
    bottom = "  |______|"
    filled_rows = ["  |######|" for _ in range(filled)]
    empty_rows = ["  |......|" for _ in range(empty)]
    bottle = [top] + (filled_rows + empty_rows)[::-1] + [bottom]

    extra_text = ""
    if extra > 0:
        extra_text = "\n💧 Extra Bottle:\n" + "\n".join([f"   🥤 Extra glass {i+1}" for i in range(extra)])

    return f"💧 Hydration Bottle:\n\n" + "\n".join(bottle) + f"\n\n{glasses}/{goal} glasses{extra_text}"

def generate_stats(user_data):
    glasses = user_data.get("glasses", 0)
    goal = user_data.get("goal", 1)
    timestamps = user_data.get("timestamps", [])
    percent = min(int((glasses / goal) * 100), 999)

    if glasses >= goal * 2:
        title = "🚀 Hydration Overlord!"
    elif glasses >= goal:
        title = "🏆 Hydration Hero!"
    elif glasses >= goal / 2:
        title = "💪 Hydration Challenger!"
    else:
        title = "🌱 Hydration Beginner"

    timeline = "\n".join([f"🥤 {i+1}. at {t}" for i, t in enumerate(timestamps)]) if timestamps else "No drinks logged yet."

    return f"{title}\n\nTotal glasses: {glasses}\nGoal: {goal}\nProgress: {percent}%\n\nTimeline:\n{timeline}"

# ------------------- دستورات -------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    in_channel = await check_user_in_channel(user_id, context.bot)

    if not in_channel:
        await update.message.reply_text(
            "To use this bot, please join our channel first.",
            reply_markup=join_keyboard
        )
        return

    await update.message.reply_text("How many glasses of water would you like to drink today?")
    context.user_data["awaiting_goal"] = True

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    text = update.message.text
    data = load_data()
    admins = load_admins()

    if context.user_data.get("awaiting_goal"):
        if not text.isdigit() or int(text) <= 0:
            await update.message.reply_text("Please enter a valid number greater than 0.")
            return

        data[user_id] = {"goal": int(text), "glasses": 0, "timestamps": []}
        save_data(data)

        is_admin = update.effective_user.id == MAIN_ADMIN_ID or update.effective_user.id in admins
        reply_markup = keyboard_admin_panel if is_admin else InlineKeyboardMarkup([[btn_drink], [btn_bottle]])

        await update.message.reply_text(
            f"Got it! Your daily goal is {text} glasses. 🚰",
            reply_markup=reply_markup
        )
        context.user_data["awaiting_goal"] = False
        return

    if context.user_data.get("awaiting_admin_add"):
        if not text.isdigit():
            await update.message.reply_text("Please enter a valid numeric user ID.")
            return
        new_admin = int(text)
        if new_admin in admins or new_admin == MAIN_ADMIN_ID:
            await update.message.reply_text("This user is already an admin.")
        else:
            admins.append(new_admin)
            save_admins(admins)
            await update.message.reply_text(f"User {new_admin} added as admin.")
        context.user_data["awaiting_admin_add"] = False
        return

    if context.user_data.get("awaiting_admin_remove"):
        if not text.isdigit():
            await update.message.reply_text("Please enter a valid numeric user ID.")
            return
        rem_admin = int(text)
        if rem_admin not in admins:
            await update.message.reply_text("This user is not an admin.")
        else:
            admins.remove(rem_admin)
            save_admins(admins)
            await update.message.reply_text(f"User {rem_admin} removed from admins.")
        context.user_data["awaiting_admin_remove"] = False
        return

    if user_id not in data:
        await update.message.reply_text("Please start first using /start.")
        return

    await update.message.reply_text("I didn't understand this message.")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    data = load_data()
    admins = load_admins()
    in_channel = await check_user_in_channel(query.from_user.id, context.bot)

    if not in_channel:
        await query.edit_message_text("You are not in the channel anymore. Please join to continue.", reply_markup=join_keyboard)
        return

    is_admin = query.from_user.id == MAIN_ADMIN_ID or query.from_user.id in admins
    reply_markup = keyboard_admin_panel if is_admin else InlineKeyboardMarkup([[btn_drink], [btn_bottle]])

    if query.data == "check_join":
        await query.edit_message_text("Awesome! You are now in the channel.")
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="How many glasses of water would you like to drink today?"
        )
        context.user_data["awaiting_goal"] = True
        return

    if user_id not in data:
        await query.edit_message_text("Please start first using /start.")
        return

    if query.data == "drink":
        data[user_id]["glasses"] += 1
        data[user_id]["timestamps"].append(datetime.now().strftime("%H:%M"))
        save_data(data)

        text = generate_bottle_text(data[user_id]["glasses"], data[user_id]["goal"])
        await query.edit_message_text(text=text, reply_markup=reply_markup)

    elif query.data == "bottle":
        bottle = generate_bottle_text(data[user_id]["glasses"], data[user_id]["goal"])
        stats = generate_stats(data[user_id])
        await query.edit_message_text(text=f"{bottle}\n\n📊 Stats:\n{stats}", reply_markup=reply_markup)

    elif query.data == "addadmin":
        if not is_admin:
            await query.edit_message_text("You are not authorized.")
            return
        await query.edit_message_text("Please send the numeric user ID you want to add as admin.")
        context.user_data["awaiting_admin_add"] = True

    elif query.data == "removeadmin":
        if not is_admin:
            await query.edit_message_text("You are not authorized.")
            return
        await query.edit_message_text("Please send the numeric user ID you want to remove from admins.")
        context.user_data["awaiting_admin_remove"] = True

    elif query.data == "show_users":
        if not is_admin:
            await query.edit_message_text("You are not authorized.")
            return
        total_users = len(data)
        user_list = "\n".join(data.keys()) if data else "No users yet."
        await query.edit_message_text(f"Total users: {total_users}\nUser IDs:\n{user_list}", reply_markup=keyboard_admin_panel)

    elif query.data == "show_admins":
        if not is_admin:
            await query.edit_message_text("You are not authorized.")
            return
        admin_list = "\n".join([str(MAIN_ADMIN_ID)] + [str(a) for a in admins]) if admins else str(MAIN_ADMIN_ID)
        await query.edit_message_text(f"Admins:\n{admin_list}", reply_markup=keyboard_admin_panel)

# ------------------- پنل ادمین از داخل callback -------------------
async def admin_panel_by_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    admins = load_admins()
    total_users = len(data)
    user_list = "\n".join(data.keys()) if data else "No users yet."
    admin_list = "\n".join([str(MAIN_ADMIN_ID)] + [str(a) for a in admins]) if admins else str(MAIN_ADMIN_ID)

    text = (
        f"👑 Admin Panel 👑\n\n"
        f"Total users: {total_users}\n"
        f"User IDs:\n{user_list}\n\n"
        f"Admins:\n{admin_list}"
    )

    await update.callback_query.edit_message_text(text, reply_markup=keyboard_admin_panel)

# ------------------- گزارش شبانه -------------------
async def scheduled_report(app):
    while True:
        now = datetime.now()
        if now.hour == 0 and now.minute == 0:
            data = load_data()
            admins = [str(MAIN_ADMIN_ID)] + [str(a) for a in load_admins()]
            report = "📊 Daily Hydration Report:\n\n"
            sent = False

            for uid, info in data.items():
                if uid in admins:
                    stats = generate_stats(info)
                    report += f"User {uid}:\n{stats}\n\n"
                    sent = True

                # ریست آمار روزانه
                data[uid]["glasses"] = 0
                data[uid]["timestamps"] = []

            save_data(data)

            if sent:
                await app.bot.send_message(chat_id=CHANNEL_USERNAME, text=report)

            # دوباره پرسش هدف جدید برای همه کاربران
            for uid in data:
                try:
                    await app.bot.send_message(
                        chat_id=int(uid),
                        text="How many glasses of water would you like to drink today?"
                    )
                except:
                    pass

            await asyncio.sleep(60)
        await asyncio.sleep(10)

# ------------------- اجرای اصلی -------------------
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("adminpanel", admin_panel_by_callback))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    import threading
    threading.Thread(target=lambda: asyncio.run(scheduled_report(app)), daemon=True).start()

    print("Bot is running...")
    app.run_polling()
