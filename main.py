import logging
import random
import os
import json
import asyncio
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# ==========================================
# 👇 কনফিগারেশন
# ==========================================
TOKEN = "8501755839:AAEzVcXuPmlPB56MpqSehkhbxzPKi9HByR8"
ADMIN_IDS = [1933498659, 6451711574, 7707686630]
CHANNEL_USERNAME = "@rsghd33"
CHANNEL_LINK = "https://t.me/rsghd33"
BOT_USERNAME = "raisa_mal_bot"

# ==========================================
# 🔥🔥🔥 ভিডিও রাখার স্থায়ী জায়গা (কোডিং এর ভেতর) 🔥🔥🔥
# ==========================================
PERMANENT_VIDEOS = {
    "BD HOT": [
        # এখানে আপনার ভিডিও আইডি বসাবেন
    ],
    "US HOT": [],
    "RI HOT": []
}

# অটো মেসেজ
BOT_START_LINK = f"https://t.me/{BOT_USERNAME}?start=hot_video"
AUTO_MESSAGES = [
    "🔥 **ভাইরাল ভিডিও!** 😱\nদেখার জন্য নিচে ক্লিক করুন 👇\n👉 " + BOT_START_LINK,
    "🔞 **উফফ! কি দেখলাম।** 🥵\nহেডফোন লাগিয়ে দেখুন 👇\n👉 " + BOT_START_LINK
]

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

    menu_buttons = [
        [KeyboardButton("🔥 BD HOT"), KeyboardButton("🇺🇸 US HOT")],
        [KeyboardButton("🌶️ RI HOT"), KeyboardButton("📢 MY OFFICIAL CHANNEL")],
        [KeyboardButton("➕ Add Me To Your Group ➕")]
    ]
    markup = ReplyKeyboardMarkup(menu_buttons, resize_keyboard=True)

    if chat_type in ['group', 'supergroup']:
        await update.message.reply_text("🔥 **Menu Loaded!** 🔥", reply_markup=markup)
        return
    
    if user_id in ADMIN_IDS:
        buttons = [[KeyboardButton("📊 Stats"), KeyboardButton("📢 Broadcast")]]
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
    pass # ডাটাবেস ছাড়া গ্রুপ লোড হবে না, তাই অটো পোস্ট বন্ধ থাকবে

# ৩. মেসেজ হ্যান্ডলার
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    
    # ভিডিও আপলোড এবং কোড জেনারেশন
    if update.message.reply_to_message and update.message.reply_to_message.video:
        if user_id not in ADMIN_IDS: return 
        video_id = update.message.reply_to_message.video.file_id
        folder = text.strip().upper()
        
        valid_folders = ["BD HOT", "US HOT", "RI HOT"]
        if folder in valid_folders:
            code_line = f'"{video_id}",'
            await update.message.reply_text(
                f"✅ **ভিডিও আইডি:**\nনিচের লাইনটি কপি করে GitHub এর `PERMANENT_VIDEOS` এর `{folder}` লিস্টে বসান:\n\n`{code_line}`",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text("❌ ফোল্ডার নাম ভুল! লিখুন: `BD HOT`, `US HOT`, `RI HOT`")
        return

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
        all_vids = PERMANENT_VIDEOS.get(folder, [])
        
        if not all_vids:
            await update.message.reply_text("❌ ভিডিও নেই।")
            return
        
        vid = random.choice(all_vids)
        try:
            await context.bot.send_video(chat_id=update.effective_chat.id, video=vid, caption=f"Join: {CHANNEL_USERNAME}")
        except: await update.message.reply_text("Error loading video.")
        return

async def video_reply_guide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in ADMIN_IDS and update.effective_chat.type == 'private':
        await update.message.reply_text("🎥 ভিডিও পেয়েছি! Reply করে নাম (BD HOT) লিখুন।")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VIDEO, video_reply_guide))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    print("🔥 SIMPLE BOT STARTED 🔥")
    app.run_polling()
