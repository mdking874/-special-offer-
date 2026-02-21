import logging
import random
import re
import requests
import json
import os
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# ---------------------------------------------------------
# ১. কনফিগারেশন
BOT_TOKEN = "8508230875:AAGEldhmFI56fkrc_O_op-epuf9gdTaezvg"
ADMIN_ID = 1933498659

# ডাটাবেস ফাইল
USERS_FILE = "users_db.json"
KEYS_FILE = "keys_db.json"

# ওয়েবসাইট লিস্ট
REGULAR_SITES = [
    "https://fry99.cc/latest-videos/", 
    "https://desibf.com/tag/desi-49/",
    "https://www.desitales2.com/videos/tag/desi49/"
]
CLEAN_PLAYER_URL = "https://hlsjs.video-dev.org/demo/?src="

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
# ---------------------------------------------------------

# --- ডাটাবেস ফাংশন ---
def load_data(filename):
    if not os.path.exists(filename): return {}
    try:
        with open(filename, 'r') as f: return json.load(f)
    except: return {}

def save_data(filename, data):
    with open(filename, 'w') as f: json.dump(data, f, indent=4)

async def is_subscribed(user_id):
    users = load_data(USERS_FILE)
    uid = str(user_id)
    if uid in users:
        expiry = datetime.strptime(users[uid], "%Y-%m-%d %H:%M:%S")
        if expiry > datetime.now(): return True, expiry
    return False, None

# --- ভিডিও স্ক্র্যাপার (র্যান্ডম ভিডিওর জন্য) ---
def get_clean_stream(page_url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(page_url, headers=headers, timeout=10)
        html = response.text
        m3u8 = re.findall(r'(https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*)', html)
        if m3u8: return CLEAN_PLAYER_URL + m3u8[0]
        mp4 = re.findall(r'(https?://[^\s"\'<>]+\.mp4)', html)
        if mp4: return mp4[0]
        return None
    except: return None

def scrape_all_videos():
    results = []
    for site in REGULAR_SITES:
        try:
            res = requests.get(site, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            for a in soup.find_all('a'):
                img = a.find('img')
                if img and a.get('href'):
                    title = (img.get('alt') or "Hot Video")
                    url = a.get('href')
                    if not url.startswith("http"):
                        url = "/".join(site.split("/")[:3]) + url
                    thumb = img.get('src') or img.get('data-src')
                    results.append({'title': title, 'url': url, 'thumb': thumb})
        except: continue
    return results

# --- কমান্ড হ্যান্ডলারস ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sub, exp = await is_subscribed(update.effective_user.id)
    if sub:
        await update.message.reply_text(f"✅ প্রিমিয়াম স্ট্যাটাস: সক্রিয়\n⏳ মেয়াদ: {exp.strftime('%Y-%m-%d')}\n\nভিডিও দেখতে 'video' লিখুন অথবা /video কমান্ড দিন।")
    else:
        await update.message.reply_text(f"🚫 সাবস্ক্রিপশন নেই।\nকি (Key) কিনতে অ্যাডমিনকে মেসেজ দিন।\n👤 অ্যাডমিন আইডি: `{ADMIN_ID}`", parse_mode='Markdown')

async def gen_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        days, slots = int(context.args[0]), int(context.args[1])
        key = f"VIP-{random.randint(100,999)}-{random.randint(100,999)}"
        keys = load_data(KEYS_FILE); keys[key] = {"days": days, "slots": slots}; save_data(KEYS_FILE, keys)
        await update.message.reply_text(f"🔑 Key: `{key}`\n⏳ Days: {days}\n👥 Slots: {slots}")
    except: await update.message.reply_text("ব্যবহার: `/gen দিন স্লট`")

async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        key_input = context.args[0]
        keys = load_data(KEYS_FILE)
        if key_input in keys:
            expiry = datetime.now() + timedelta(days=keys[key_input]['days'])
            users = load_data(USERS_FILE); users[str(update.effective_user.id)] = expiry.strftime("%Y-%m-%d %H:%M:%S"); save_data(USERS_FILE, users)
            if keys[key_input]['slots'] > 1: keys[key_input]['slots'] -= 1
            else: del keys[key_input]
            save_data(KEYS_FILE, keys)
            await update.message.reply_text(f"🎉 প্রিমিয়াম সফল! মেয়াদ: {expiry.strftime('%Y-%m-%d')}")
        else: await update.message.reply_text("❌ ভুল বা মেয়াদী কি।")
    except: await update.message.reply_text("ব্যবহার: `/redeem YOUR_KEY`")

# --- ভিডিও হ্যান্ডলার (সার্চ বাদ দিয়ে সরাসরি ভিডিও) ---
async def video_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.lower()
    
    # শুধু 'video' শব্দ অথবা '/video' কমান্ড হলে কাজ করবে
    if text != "video" and not text.startswith("/video"):
        return

    sub, _ = await is_subscribed(uid)
    if not sub:
        await update.message.reply_text("🚫 আগে সাবস্ক্রিপশন নিন।")
        return

    await update.message.reply_text("🎥 ভিডিও তৈরি হচ্ছে, অপেক্ষা করুন...")
    
    all_videos = scrape_all_videos()
    if not all_videos:
        await update.message.reply_text("❌ এই মুহূর্তে কোনো ভিডিও পাওয়া যায়নি।")
        return

    random.shuffle(all_videos)
    found = False

    for v in all_videos[:20]: # ২০টি ভিডিওর মধ্যে চেক করবে
        clean = get_clean_stream(v['url'])
        if clean:
            caption = f"🎬 **{v['title']}**\n🛡️ Status: Ad-Free Ready ✅\n\n▶️ [Click to Play]({clean})"
            try:
                await update.message.reply_photo(photo=v['thumb'] or "https://via.placeholder.com/400", caption=caption, parse_mode='Markdown')
                found = True; break
            except:
                await update.message.reply_text(caption, parse_mode='Markdown')
                found = True; break
    
    if not found:
        await update.message.reply_text("⚠️ সরাসরি প্লে করার মতো ভিডিও লিংক পাওয়া যায়নি। আবার চেষ্টা করুন।")

# --- মেইন ---
if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("gen", gen_key))
    app.add_handler(CommandHandler("redeem", redeem))
    app.add_handler(CommandHandler("video", video_handler)) # /video কমান্ডের জন্য
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), video_handler)) # শুধু 'video' লেখার জন্য
    
    print("Bot is running...")
    app.run_polling()
