import logging
import random
import os
import json
import asyncio
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, ChatMemberHandler
import pymongo 

# ==========================================
# 👇 কনফিগারেশন
# ==========================================
TOKEN = "8501755839:AAEzVcXuPmlPB56MpqSehkhbxzPKi9HByR8"
ADMIN_IDS = [1933498659, 6451711574, 7707686630]
CHANNEL_USERNAME = "@rsghd33"
CHANNEL_LINK = "https://t.me/rsghd33"
BOT_USERNAME = "raisa_mal_bot"

# 👇 MongoDB লিংক (অপশনাল, তবে ব্যাকআপের জন্য ভালো)
MONGO_URL = "আপনার_মঙ্গোডিবি_লিংক_এখানে_দিন"

# ==========================================
# 🔥🔥🔥 ভিডিও রাখার স্থায়ী জায়গা (কোডিং এর ভেতর) 🔥🔥🔥
# আপনি টেলিগ্রামে ভিডিও আপলোড করলে বোট যে আইডি দিবে, সেটা কপি করে এখানে বসাবেন।
# ==========================================
PERMANENT_VIDEOS = {
    "BD HOT": [
        "এখানে_আপনার_ভিডিও_আইডি_বসাতে_পারেন_1",
        "এখানে_আপনার_ভিডিও_আইডি_বসাতে_পারেন_2",
    ],
    "US HOT": [
        "us_video_id_1",
    ],
    "RI HOT": [
        "ri_video_id_1",
    ]
}
# ==========================================

# MongoDB কানেকশন (যদি লিংক থাকে তবেই কানেক্ট হবে, নাহলে এরর দিবে না)
try:
    client = pymongo.MongoClient(MONGO_URL)
    db = client["TelegramBotDB"]
    users_col = db["users"]
    groups_col = db["groups"]
    videos_col = db["videos"] # এক্সট্রা ব্যাকআপ
    history_col = db["history"]
    mongo_active = True
except:
    mongo_active = False # মঙ্গোডিবি না থাকলে শুধু কোডিং এর ভিডিও চলবে

# অটো মেসেজ
BOT_START_LINK = f"https://t.me/{BOT_USERNAME}?start=hot_video"
AUTO_MESSAGES = [
    "🔥 **ভাইরাল ভিডিও!** 😱\nদেখার জন্য নিচে ক্লিক করুন 👇\n👉 " + BOT_START_LINK,
    "🔞 **উফফ! কি দেখলাম।** 🥵\nহেডফোন লাগিয়ে দেখুন 👇\n👉 " + BOT_START_LINK,
    "💋 **কলেজের ভিডিও লিক!** 🙈\nমিস করবেন না 👇\n👉 " + BOT_START_LINK
]

# ==========================================
# 👇 ফাংশনসমূহ
# ==========================================

# সব ভিডিও একত্রে করা (কোডিং + ডাটাবেস)
def get_all_videos(folder):
    # ১. কোড থেকে ভিডিও নেওয়া
    code_vids = PERMANENT_VIDEOS.get(folder, [])
    
    # ২. ডাটাবেস থেকে ভিডিও নেওয়া (যদি থাকে)
    mongo_vids = []
    if mongo_active:
        vids = videos_col.find({"folder": folder})
        mongo_vids = [v["file_id"] for v in vids]
    
    # ৩. দুইটা মিক্স করা (ডুপ্লিকেট বাদ দিয়ে)
    return list(set(code_vids + mongo_vids))

# ইউজার ও গ্রুপ সেভ (MongoDB তে)
def add_user(user_id):
    if mongo_active and not users_col.find_one({"_id": user_id}):
        users_col.insert_one({"_id": user_id})

def add_group(chat_id):
    if mongo_active and not groups_col.find_one({"_id": chat_id}):
        groups_col.insert_one({"_id": chat_id})

# মেম্বারশিপ চেক
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

    # মেনু
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
        buttons = [[KeyboardButton("📊 Stats"), KeyboardButton("📢 Broadcast")]]
        await update.message.reply_text(f"👑 **Admin Panel**\nভিডিও আপলোড করলে কোড জেনারেট হবে।", reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))
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
    if not mongo_active: return
    all_groups = groups_col.find({})
    msg = random.choice(AUTO_MESSAGES)
    for grp in all_groups:
        try: await context.bot.send_message(chat_id=grp["_id"], text=msg, parse_mode='Markdown')
        except: pass

# ৩. মেসেজ হ্যান্ডলার
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_type = update.effective_chat.type
    if chat_type in ['group', 'supergroup']: add_group(update.effective_chat.id)
    
    text = update.message.text
    user_id = update.effective_user.id
    
    # 🔥 ভিডিও আপলোড এবং কোড জেনারেশন 🔥
    if update.message.reply_to_message and update.message.reply_to_message.video:
        if user_id not in ADMIN_IDS: return 
        video_id = update.message.reply_to_message.video.file_id
        folder = text.strip().upper()
        
        valid_folders = ["BD HOT", "US HOT", "RI HOT"]
        if folder in valid_folders:
            # ১. মঙ্গোডিবিতে সেভ (তাৎক্ষণিক ব্যবহারের জন্য)
            if mongo_active:
                if not videos_col.find_one({"folder": folder, "file_id": video_id}):
                    videos_col.insert_one({"folder": folder, "file_id": video_id})
            
            # ২. কোড জেনারেট করে দেওয়া (পার্মানেন্ট করার জন্য)
            code_line = f'"{video_id}",'
            
            await update.message.reply_text(
                f"✅ **ভিডিওটি সাময়িকভাবে সেভ হয়েছে!**\n\nতবে এটাকে **স্থায়ীভাবে কোডিং-এ রাখতে** হলে নিচের লাইনটি কপি করে GitHub এর `PERMANENT_VIDEOS` এর `{folder}` লিস্টে বসান:\n\n`{code_line}`",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text("❌ ফোল্ডার নাম ভুল! লিখুন: `BD HOT`, `US HOT`, `RI HOT`")
        return

    # এডমিন স্ট্যাটস
    if user_id in ADMIN_IDS and text == "📊 Stats":
        msg = "📊 **ভিডিও স্ট্যাটাস:**\n"
        for f in ["BD HOT", "US HOT", "RI HOT"]:
            count = len(get_all_videos(f))
            msg += f"{f}: {count} টি\n"
        await update.message.reply_text(msg)
        return

    # বাটন লজিক
    if text == "➕ Add Me To Your Group ➕":
        url = f"https://t.me/{context.bot.username}?startgroup=true"
        await update.message.reply_text("👇 গ্রুপে অ্যাড করুন:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🚀 Add", url=url)]]))
        return
    
    if text == "📢 MY OFFICIAL CHANNEL":
        await update.message.reply_text(f"Join: {CHANNEL_LINK}")
        return

    # ভিডিও পাঠানো
    folder_map = {"🔥 BD HOT": "BD HOT", "🇺🇸 US HOT": "US HOT", "🌶️ RI HOT": "RI HOT"}
    if text in folder_map:
        if not await check_membership(user_id, context):
            await update.message.reply_text("⚠️ **লক করা!** আগে জয়েন করুন।", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Join 🔞", url=CHANNEL_LINK)]]))
            return
        
        folder = folder_map[text]
        all_vids = get_all_videos(folder)
        
        if not all_vids:
            await update.message.reply_text("❌ ভিডিও নেই।")
            return
        
        # নো-রিপিট লজিক (হিস্ট্রি চেক)
        seen_vids = []
        if mongo_active:
            data = history_col.find_one({"_id": user_id})
            if data and folder in data: seen_vids = data[folder]

        available = [v for v in all_vids if v not in seen_vids]
        if not available:
            seen_vids = [] # রিসেট
            available = all_vids
            if mongo_active: history_col.update_one({"_id": user_id}, {"$set": {folder: []}})
        
        vid = random.choice(available)
        try:
            await context.bot.send_video(chat_id=update.effective_chat.id, video=vid, caption=f"Join: {CHANNEL_USERNAME}")
            if mongo_active:
                history_col.update_one({"_id": user_id}, {"$push": {folder: vid}}, upsert=True)
        except: await update.message.reply_text("Error loading video.")
        return

async def video_reply_guide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in ADMIN_IDS and update.effective_chat.type == 'private':
        await update.message.reply_text("🎥 ভিডিও পেয়েছি! Reply করে নাম (BD HOT) লিখুন।")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.job_queue.run_repeating(send_auto_group_messages, interval=14400, first=10)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VIDEO, video_reply_guide))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    print("🔥 HYBRID BOT STARTED 🔥")
    app.run_polling()
