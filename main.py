import logging
import random
import os
import asyncio
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import pymongo 

# ==========================================
# 👇 কনফিগারেশন (আপনার তথ্য দিন)
# ==========================================
TOKEN = "8501755839:AAEzVcXuPmlPB56MpqSehkhbxzPKi9HByR8"
ADMIN_IDS = [1933498659, 6451711574, 7707686630]
CHANNEL_USERNAME = "@rsghd33"
CHANNEL_LINK = "https://t.me/rsghd33"
BOT_USERNAME = "raisa_mal_bot"

# 👇 আপনার দেওয়া MongoDB লিংক (আমি বসিয়ে দিয়েছি) ✅
MONGO_URL = "mongodb+srv://rapem9312:Mdrafiking123@cluster0.e27uvmy.mongodb.net/?appName=Cluster0"

# ==========================================
# 🔥 ডাটাবেস কানেকশন
# ==========================================
mongo_active = False
try:
    client = pymongo.MongoClient(MONGO_URL)
    db = client["TelegramBotDB"]
    users_col = db["users"]
    groups_col = db["groups"]
    videos_col = db["videos"] 
    history_col = db["history"]
    mongo_active = True
    print("✅ Database Connected Successfully!")
except Exception as e:
    print(f"❌ Database Connection Failed: {e}")

# এডমিনদের আপলোড মোড
ADMIN_UPLOAD_MODE = {}

# অটো মেসেজ (গ্রুপের জন্য)
BOT_START_LINK = f"https://t.me/{BOT_USERNAME}?start=hot_video"
AUTO_MESSAGES = [
    "🔥 **ভাইরাল ভিডিও!** 😱\nদেখার জন্য নিচে ক্লিক করুন 👇\n👉 " + BOT_START_LINK,
    "🔞 **উফফ! কি দেখলাম।** 🥵\nহেডফোন লাগিয়ে দেখুন 👇\n👉 " + BOT_START_LINK,
    "💋 **কলেজের ভিডিও লিক!** 🙈\nমিস করবেন না 👇\n👉 " + BOT_START_LINK
]

# ==========================================
# 👇 ফাংশনসমূহ
# ==========================================

def add_user(user_id):
    if mongo_active and not users_col.find_one({"_id": user_id}):
        users_col.insert_one({"_id": user_id})

def add_group(chat_id):
    if mongo_active and not groups_col.find_one({"_id": chat_id}):
        groups_col.insert_one({"_id": chat_id})

# 🔥 ভিডিও অটো সেভ ফাংশন 🔥
def auto_save_video(folder, file_id):
    if not mongo_active: return False
    if not videos_col.find_one({"folder": folder, "file_id": file_id}):
        videos_col.insert_one({"folder": folder, "file_id": file_id})
        return True
    return False

def get_videos(folder):
    if not mongo_active: return []
    vids = videos_col.find({"folder": folder})
    return [v["file_id"] for v in vids]

async def check_membership(user_id, context):
    if user_id in ADMIN_IDS: return True
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status in ['left', 'kicked', 'banned']: return False
        return True
    except: return True 

# ==========================================
# ১. স্টার্ট কমান্ড
# ==========================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_type = update.effective_chat.type

    # গ্রুপ মেনু
    if chat_type in ['group', 'supergroup']:
        add_group(update.effective_chat.id)
        menu_buttons = [
            [KeyboardButton("🔥 BD HOT"), KeyboardButton("🇺🇸 US HOT")],
            [KeyboardButton("🌶️ RI HOT"), KeyboardButton("📢 MY OFFICIAL CHANNEL")],
            [KeyboardButton("➕ Add Me To Your Group ➕")]
        ]
        await update.message.reply_text("🔥 **Menu Loaded!** 🔥", reply_markup=ReplyKeyboardMarkup(menu_buttons, resize_keyboard=True))
        return

    add_user(user_id)
    
    # এডমিন প্যানেল
    if user_id in ADMIN_IDS:
        if user_id in ADMIN_UPLOAD_MODE: del ADMIN_UPLOAD_MODE[user_id]
        buttons = [
            [KeyboardButton("📤 Start Auto Upload"), KeyboardButton("📊 Database Stats")],
            [KeyboardButton("👥 User Mode"), KeyboardButton("📢 Broadcast")]
        ]
        status = "✅ Connected" if mongo_active else "❌ Not Connected"
        await update.message.reply_text(
            f"👑 **Admin Panel**\nDB Status: {status}\nভিডিও আপলোড করতে **'Start Auto Upload'** এ ক্লিক করুন।",
            reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True)
        )
        return

    # সাধারণ ইউজার
    if not await check_membership(user_id, context):
        join_btn = [[InlineKeyboardButton("🔞 JOIN TO WATCH 🔞", url=CHANNEL_LINK)]]
        await update.message.reply_text("⚠️ **ভিডিও লক করা!** আগে জয়েন করুন। 👇", reply_markup=InlineKeyboardMarkup(join_btn))
        return

    welcome_text = "🔥 **আগুন সব ভিডিওর ভান্ডারে স্বাগতম!** 🔥\n🚀 **দেরি না করে এখনই আমাকে আপনার গ্রুপে অ্যাড করুন!** 👇"
    add_link = f"https://t.me/{context.bot.username}?startgroup=true"
    inline_btn = [[InlineKeyboardButton("➕ Add Me To Your Group ➕", url=add_link)], [InlineKeyboardButton("Join Channel 🚀", url=CHANNEL_LINK)]]
    
    menu_buttons = [
        [KeyboardButton("🔥 BD HOT"), KeyboardButton("🇺🇸 US HOT")],
        [KeyboardButton("🌶️ RI HOT"), KeyboardButton("📢 MY OFFICIAL CHANNEL")],
        [KeyboardButton("➕ Add Me To Your Group ➕")]
    ]
    
    await update.message.reply_text(welcome_text, reply_markup=InlineKeyboardMarkup(inline_btn))
    await update.message.reply_text("অথবা ক্যাটাগরি বেছে নিন: 👇", reply_markup=ReplyKeyboardMarkup(menu_buttons, resize_keyboard=True))

# ==========================================
# ২. অটো পোস্ট (গ্রুপে)
# ==========================================
async def send_auto_group_messages(context: ContextTypes.DEFAULT_TYPE):
    if not mongo_active: return
    groups = groups_col.find({})
    msg = random.choice(AUTO_MESSAGES)
    count = 0
    for grp in groups:
        try:
            await context.bot.send_message(chat_id=grp["_id"], text=msg, parse_mode='Markdown')
            count += 1
        except: pass
    print(f"Auto-posted to {count} groups.")

# ==========================================
# ৩. মেইন লজিক (ভিডিও আপলোড + দেখা)
# ==========================================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    
    # 🔥🔥🔥 অটোমেটিক ভিডিও সেভ 🔥🔥🔥
    if update.message.video or (update.message.reply_to_message and update.message.reply_to_message.video):
        if user_id not in ADMIN_IDS: return 
        
        video_id = update.message.video.file_id if update.message.video else update.message.reply_to_message.video.file_id
        
        if user_id in ADMIN_UPLOAD_MODE:
            folder = ADMIN_UPLOAD_MODE[user_id]
            if auto_save_video(folder, video_id):
                await update.message.reply_text(f"✅ Saved to **{folder}**", quote=True, parse_mode='Markdown')
            else:
                await update.message.reply_text(f"⚠️ Already in **{folder}**", quote=True, parse_mode='Markdown')
        else:
            await update.message.reply_text("⚠️ **ফোল্ডার সেট করা নেই!**\nএডমিন প্যানেল থেকে 'Start Auto Upload' এ ক্লিক করুন।")
        return

    # --- এডমিন বাটন ---
    if user_id in ADMIN_IDS:
        if text == "📤 Start Auto Upload":
            buttons = [
                [KeyboardButton("SET: BD HOT"), KeyboardButton("SET: US HOT")],
                [KeyboardButton("SET: RI HOT"), KeyboardButton("❌ Stop Uploading")]
            ]
            await update.message.reply_text("📂 **কোন ফোল্ডারে সেভ করবেন?**", reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))
            return
        
        elif text and text.startswith("SET: "):
            folder = text.replace("SET: ", "")
            ADMIN_UPLOAD_MODE[user_id] = folder
            await update.message.reply_text(f"✅ **Auto Save ON: {folder}**\nএখন ভিডিও ফরোয়ার্ড করুন।")
            return
            
        elif text == "❌ Stop Uploading":
            if user_id in ADMIN_UPLOAD_MODE: del ADMIN_UPLOAD_MODE[user_id]
            buttons = [[KeyboardButton("📤 Start Auto Upload"), KeyboardButton("📊 Database Stats")], [KeyboardButton("👥 User Mode")]]
            await update.message.reply_text("⏹️ **বন্ধ করা হয়েছে।**", reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))
            return

        elif text == "📊 Database Stats":
            if not mongo_active:
                await update.message.reply_text("❌ Database Not Connected!")
                return
            msg = "📊 **ডাটাবেস রিপোর্ট:**\n"
            for f in ["BD HOT", "US HOT", "RI HOT"]:
                count = videos_col.count_documents({"folder": f})
                msg += f"🔹 {f}: {count} টি\n"
            msg += f"\n👥 ইউজার: {users_col.count_documents({})}"
            await update.message.reply_text(msg, parse_mode='Markdown')
            return

        elif text == "👥 User Mode":
            menu_buttons = [
                [KeyboardButton("🔥 BD HOT"), KeyboardButton("🇺🇸 US HOT")],
                [KeyboardButton("🌶️ RI HOT"), KeyboardButton("📢 MY OFFICIAL CHANNEL")],
                [KeyboardButton("➕ Add Me To Your Group ➕")]
            ]
            await update.message.reply_text("User Mode On", reply_markup=ReplyKeyboardMarkup(menu_buttons, resize_keyboard=True))
            return

    # --- সাধারণ বাটন ---
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
        all_vids = get_videos(folder)
        
        if not all_vids:
            await update.message.reply_text("❌ ভিডিও নেই।")
            return
        
        # নো-রিপিট লজিক
        user_history = history_col.find_one({"_id": user_id}) or {}
        seen = user_history.get(folder, [])
        
        available = [v for v in all_vids if v not in seen]
        if not available:
            history_col.update_one({"_id": user_id}, {"$set": {folder: []}})
            available = all_vids
        
        vid = random.choice(available)
        try:
            await context.bot.send_video(chat_id=update.effective_chat.id, video=vid, caption=f"Join: {CHANNEL_USERNAME}")
            history_col.update_one({"_id": user_id}, {"$push": {folder: vid}}, upsert=True)
        except: await update.message.reply_text("Error loading video.")
        return

# ব্রডকাস্ট হ্যান্ডলার
async def broadcast_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    msg = " ".join(context.args)
    if not msg: 
        await update.message.reply_text("Use: `/broadcast msg`")
        return
    users = users_col.find({})
    await update.message.reply_text(f"Sending...")
    for u in users:
        try: await context.bot.send_message(u["_id"], msg)
        except: pass
    await update.message.reply_text("Done.")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.job_queue.run_repeating(send_auto_group_messages, interval=14400, first=10)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("broadcast", broadcast_users))
    app.add_handler(MessageHandler(filters.ALL, handle_message))
    print("🔥 FINAL MONGO BOT STARTED 🔥")
    app.run_polling()
