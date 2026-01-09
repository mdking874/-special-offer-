import logging
import random
import os
import json
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, ChatMemberHandler

# ==========================================
# 👇 কনফিগারেশন
# ==========================================
TOKEN = "8501755839:AAEzVcXuPmlPB56MpqSehkhbxzPKi9HByR8" 
ADMIN_IDS = [1933498659, 6451711574, 7707686630] 
CHANNEL_USERNAME = "@rsghd33"
CHANNEL_LINK = "https://t.me/rsghd33"
BOT_USERNAME = "raisa_mal_bot" # আপনার বোটের ইউজারনেম

# ==========================================
# 🔥 ফাইল এবং ডাটাবেস
# ==========================================
DB_FILE = "video_database.json" 
USER_DB_FILE = "users_db.json"
GROUP_DB_FILE = "groups_db.json"
HISTORY_FILE = "history.json"

AUTO_MESSAGES = [
    "🔥 **ভাইরাল ভিডিও!** 😱\nদেখার জন্য নিচে ক্লিক করুন 👇\nhttps://t.me/" + BOT_USERNAME + "?start=hot_video",
    "🔞 **উফফ! কি দেখলাম।** 🥵\nহেডফোন লাগিয়ে দেখুন 👇\nhttps://t.me/" + BOT_USERNAME + "?start=hot_video",
    "💋 **কলেজের ভিডিও লিক!** 🙈\nমিস করবেন না 👇\nhttps://t.me/" + BOT_USERNAME + "?start=hot_video"
]

# ডাটা লোড/সেভ ফাংশন
def load_data(filename):
    if not os.path.exists(filename): return {} if filename in [DB_FILE, HISTORY_FILE] else []
    try:
        with open(filename, 'r') as f: return json.load(f)
    except: return {} if filename in [DB_FILE, HISTORY_FILE] else []

def save_data(filename, data):
    with open(filename, 'w') as f: json.dump(data, f, indent=4)

def add_user(user_id):
    users = load_data(USER_DB_FILE)
    if user_id not in users:
        users.append(user_id)
        save_data(USER_DB_FILE, users)

def add_group(chat_id):
    groups = load_data(GROUP_DB_FILE)
    if chat_id not in groups:
        groups.append(chat_id)
        save_data(GROUP_DB_FILE, groups)

# মেম্বারশিপ চেক
async def check_membership(user_id, context):
    if user_id in ADMIN_IDS: return True
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status in ['left', 'kicked', 'banned']: return False
        return True
    except: return True 

# ১. স্টার্ট কমান্ড
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_type = update.effective_chat.type

    # মেনু বাটন
    menu_buttons = [
        [KeyboardButton("🔥 BD HOT"), KeyboardButton("🇺🇸 US HOT")],
        [KeyboardButton("🌶️ RI HOT"), KeyboardButton("📢 MY OFFICIAL CHANNEL")],
        [KeyboardButton("➕ Add Me To Your Group ➕")]
    ]
    markup = ReplyKeyboardMarkup(menu_buttons, resize_keyboard=True)

    if chat_type in ['group', 'supergroup']:
        add_group(update.effective_chat.id)
        await update.message.reply_text("🔥 **Menu Loaded!** 🔥", reply_markup=markup)
        return

    add_user(user_id)
    
    if user_id in ADMIN_IDS:
        buttons = [[KeyboardButton("📊 Stats"), KeyboardButton("📢 Broadcast Users")], [KeyboardButton("📢 Broadcast Groups")]]
        await update.message.reply_text(f"👑 **Admin Panel**", reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))
        return

    if not await check_membership(user_id, context):
        join_btn = [[InlineKeyboardButton("🔞 JOIN TO WATCH 🔞", url=CHANNEL_LINK)]]
        await update.message.reply_text("⚠️ **ভিডিও লক করা!** আগে জয়েন করুন। 👇", reply_markup=InlineKeyboardMarkup(join_btn))
        return

    welcome_text = "🔥 **আগুন সব ভিডিওর ভান্ডারে স্বাগতম!** 🔥\n🚀 **দেরি না করে এখনই আমাকে আপনার গ্রুপে অ্যাড করুন!** 👇"
    add_link = f"https://t.me/{context.bot.username}?startgroup=true"
    inline_btn = [[InlineKeyboardButton("➕ Add Me To Your Group ➕", url=add_link)], [InlineKeyboardButton("Join Channel 🚀", url=CHANNEL_LINK)]]
    
    await update.message.reply_text(welcome_text, reply_markup=InlineKeyboardMarkup(inline_btn))
    await update.message.reply_text("অথবা ক্যাটাগরি বেছে নিন: 👇", reply_markup=markup)

# ২. অটো পোস্ট
async def send_auto_group_messages(context: ContextTypes.DEFAULT_TYPE):
    groups = load_data(GROUP_DB_FILE)
    if not groups: return
    msg = random.choice(AUTO_MESSAGES)
    for chat_id in groups:
        try: await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode='Markdown')
        except: pass

# ৩. মেসেজ হ্যান্ডলার
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in ['group', 'supergroup']: add_group(update.effective_chat.id)
    text = update.message.text
    user_id = update.effective_user.id
    
    # ভিডিও সেভ
    if update.message.reply_to_message and update.message.reply_to_message.video:
        if user_id not in ADMIN_IDS: return 
        vid_id = update.message.reply_to_message.video.file_id
        folder = text.strip().upper()
        if folder in ["BD HOT", "US HOT", "RI HOT"]:
            db = load_data(DB_FILE)
            if folder not in db: db[folder] = []
            if vid_id not in db[folder]:
                db[folder].append(vid_id)
                save_data(DB_FILE, db)
                await update.message.reply_text(f"✅ Saved to {folder}!")
            else: await update.message.reply_text("⚠️ Already exists.")
        return

    # এডমিন কমান্ড
    if user_id in ADMIN_IDS and update.effective_chat.type == 'private':
        if text == "📊 Stats":
            u = len(load_data(USER_DB_FILE))
            g = len(load_data(GROUP_DB_FILE))
            v = sum(len(x) for x in load_data(DB_FILE).values())
            await update.message.reply_text(f"Users: {u} | Groups: {g} | Videos: {v}")
            return
        elif text == "📢 Broadcast Users":
            await update.message.reply_text("Use: `/broadcast_users msg`")
            return
        elif text == "📢 Broadcast Groups":
            await update.message.reply_text("Use: `/broadcast_groups msg`")
            return

    # বাটন ও ভিডিও
    if text == "➕ Add Me To Your Group ➕":
        url = f"https://t.me/{context.bot.username}?startgroup=true"
        await update.message.reply_text("👇 গ্রুপে অ্যাড করুন:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🚀 Add", url=url)]]))
        return
    
    if text == "📢 MY OFFICIAL CHANNEL":
        await update.message.reply_text(f"Join: {CHANNEL_LINK}")
        return

    folder_map = {"🔥 BD HOT": "BD HOT", "🇺🇸 US HOT": "US HOT", "🌶️ RI HOT": "RI HOT"}
    if text in folder_map:
        if not await check_membership(user_id, context):
            await update.message.reply_text("⚠️ **লক করা!** আগে জয়েন করুন।", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Join 🔞", url=CHANNEL_LINK)]]))
            return
        folder = folder_map[text]
        vids = load_data(DB_FILE).get(folder, [])
        if not vids:
            await update.message.reply_text("❌ ভিডিও নেই।")
            return
        
        hist = load_data(HISTORY_FILE)
        user_h = hist.get(str(user_id), {}).get(folder, [])
        avail = [v for v in vids if v not in user_h]
        if not avail: 
            user_h = []
            avail = vids
        
        vid = random.choice(avail)
        try:
            await context.bot.send_video(chat_id=update.effective_chat.id, video=vid, caption=f"Join: {CHANNEL_USERNAME}")
            user_h.append(vid)
            if str(user_id) not in hist: hist[str(user_id)] = {}
            hist[str(user_id)][folder] = user_h
            save_data(HISTORY_FILE, hist)
        except: await update.message.reply_text("Error loading video.")
        return

# ব্রডকাস্ট
async def b_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    msg = " ".join(context.args)
    if msg:
        users = load_data(USER_DB_FILE)
        await update.message.reply_text(f"Sending to {len(users)} users...")
        for u in users:
            try: await context.bot.send_message(u, msg)
            except: pass
        await update.message.reply_text("Done.")

async def b_groups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    msg = " ".join(context.args)
    if msg:
        groups = load_data(GROUP_DB_FILE)
        await update.message.reply_text(f"Sending to {len(groups)} groups...")
        for g in groups:
            try: await context.bot.send_message(g, msg)
            except: pass
        await update.message.reply_text("Done.")

async def video_reply_guide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in ADMIN_IDS and update.effective_chat.type == 'private':
        await update.message.reply_text("🎥 ভিডিও পেয়েছি! Reply করে নাম (BD HOT) লিখুন।")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.job_queue.run_repeating(send_auto_group_messages, interval=14400, first=10)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("broadcast_users", b_users))
    app.add_handler(CommandHandler("broadcast_groups", b_groups))
    app.add_handler(MessageHandler(filters.VIDEO, video_reply_guide))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    print("🔥 BOT STARTED ON GSM HOST 🔥")
    app.run_polling()
