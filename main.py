import logging
import random
import re
import requests
import json
import os
import time
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# ---------------------------------------------------------
# ১. কনফিগারেশন
BOT_TOKEN = "8508230875:AAGEldhmFI56fkrc_O_op-epuf9gdTaezvg"
ADMIN_ID = 1933498659

# ডাটাবেস ফাইলসমূহ
USERS_FILE = "users_db.json"
KEYS_FILE = "keys_db.json"
HISTORY_FILE = "video_history.json"
SITES_FILE = "sites_db.json" # ওয়েবসাইট সেভ রাখার ফাইল

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

# ওয়েবসাইট ডাটাবেস ইনিশিয়ালাইজ (প্রথমবার রান করলে আপনার আগের সাইটগুলো অ্যাড হবে)
def init_sites():
    if not os.path.exists(SITES_FILE):
        default_sites = {
            "https://fry99.cc/": 30,
            "https://desibp1.com/": 30,
            "https://desibf.com/tag/desi-49/": 30,
            "https://www.desitales2.com/videos/tag/desi49/": 30
        }
        save_data(SITES_FILE, default_sites)

init_sites()

async def is_subscribed(user_id):
    users = load_data(USERS_FILE)
    uid = str(user_id)
    if uid in users:
        expiry = datetime.strptime(users[uid], "%Y-%m-%d %H:%M:%S")
        if expiry > datetime.now(): return True, expiry
    return False, None

# --- ভিডিও স্ট্রিম ক্লিনার ---
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

# --- ডাইনামিক পেজ জেনারেটর ও স্ক্র্যাপার ---
def scrape_random_batch():
    results = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    sites_config = load_data(SITES_FILE)
    
    all_pages = []
    for base_url, page_count in sites_config.items():
        all_pages.append(base_url) # ১ম পেজ
        for i in range(2, page_count + 1):
            # পেজ ফরম্যাট হ্যান্ডেল করা (শেষে / থাকলে বা না থাকলে)
            p_url = base_url if base_url.endswith("/") else base_url + "/"
            all_pages.append(f"{p_url}page/{i}/")

    # র্যান্ডম ১০টি পেজ সিলেক্ট করা
    sampled_sites = random.sample(all_pages, min(len(all_pages), 10))
    
    for site in sampled_sites:
        try:
            res = requests.get(site, headers=headers, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            for a in soup.find_all('a'):
                img = a.find('img')
                if img and a.get('href') and len(a.get('href')) > 20:
                    title = (img.get('alt') or "Hot Video")
                    url = a.get('href')
                    thumb = img.get('src') or img.get('data-src') or img.get('data-original')
                    if not url.startswith("http"):
                        base = "/".join(site.split("/")[:3])
                        url = base + url if url.startswith("/") else base + "/" + url
                    results.append({'title': title, 'url': url, 'thumb': thumb})
        except: continue
    return results

# --- অ্যাডমিন কমান্ড: নতুন সাইট যোগ করা ---
async def add_site(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        new_url = context.args[0]
        pages = int(context.args[1])
        sites = load_data(SITES_FILE)
        sites[new_url] = pages
        save_data(SITES_FILE, sites)
        await update.message.reply_text(f"✅ নতুন ওয়েবসাইট যুক্ত হয়েছে!\n🔗 সাইট: {new_url}\n📄 পেজ সংখ্যা: {pages}")
    except:
        await update.message.reply_text("ব্যবহার: `/addsite [URL] [Pages]`\nউদাহরণ: `/addsite https://newsite.com/ 20`", parse_mode='Markdown')

async def list_sites(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    sites = load_data(SITES_FILE)
    msg = "🌐 **বর্তমান ওয়েবসাইট লিস্ট:**\n\n"
    for url, pg in sites.items():
        msg += f"🔹 {url} (Pages: {pg})\n"
    await update.message.reply_text(msg, parse_mode='Markdown', disable_web_page_preview=True)

# --- আগের কমান্ডসমূহ ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sub, exp = await is_subscribed(update.effective_user.id)
    if sub:
        await update.message.reply_text(f"✅ প্রিমিয়াম সক্রিয়। মেয়াদ: {exp.strftime('%Y-%m-%d')}\n\nভিডিও: 'video' লিখুন।")
    else:
        await update.message.reply_text(f"🚫 সাবস্ক্রিপশন নেই। অ্যাডমিন: `{ADMIN_ID}`", parse_mode='Markdown')

async def gen_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        days, slots = int(context.args[0]), int(context.args[1])
        key = f"VIP-{random.randint(100,999)}-{random.randint(100,999)}"
        keys = load_data(KEYS_FILE); keys[key] = {"days": days, "slots": slots}; save_data(KEYS_FILE, keys)
        await update.message.reply_text(f"🔑 Key: `{key}`")
    except: await update.message.reply_text("/gen [দিন] [স্লট]")

async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        key_input = context.args[0]
        keys = load_data(KEYS_FILE)
        if key_input in keys:
            exp = datetime.now() + timedelta(days=keys[key_input]['days'])
            users = load_data(USERS_FILE); users[str(update.effective_user.id)] = exp.strftime("%Y-%m-%d %H:%M:%S"); save_data(USERS_FILE, users)
            if keys[key_input]['slots'] > 1: keys[key_input]['slots'] -= 1
            else: del keys[key_input]
            save_data(KEYS_FILE, keys)
            await update.message.reply_text("🎉 প্রিমিয়াম সফল!")
    except: pass

async def content_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    text = update.message.text.lower() if update.message.text else ""
    sub, _ = await is_subscribed(uid)
    if not sub: return

    if "video" in text:
        await update.message.reply_text("🎥 ভিডিও খোঁজা হচ্ছে...")
        batch = scrape_random_batch()
        history_db = load_data(HISTORY_FILE)
        user_history = history_db.get(uid, {})
        random.shuffle(batch)
        for v in batch:
            if v['url'] in user_history and time.time() - user_history[v['url']] < 172800: continue
            clean = get_clean_stream(v['url'])
            if clean:
                user_history[v['url']] = time.time(); history_db[uid] = user_history; save_data(HISTORY_FILE, history_db)
                try:
                    await update.message.reply_photo(photo=v['thumb'] or "https://via.placeholder.com/400", caption=f"🎬 {v['title']}\n\n▶️ [Watch Ad-Free]({clean})", parse_mode='Markdown')
                except:
                    await update.message.reply_text(f"🎬 {v['title']}\n\n▶️ [Watch Ad-Free]({clean})", parse_mode='Markdown')
                return
        await update.message.reply_text("🕒 পরে চেষ্টা করুন।")

# --- রানার ---
if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("gen", gen_key))
    app.add_handler(CommandHandler("redeem", redeem))
    app.add_handler(CommandHandler("addsite", add_site)) # নতুন সাইট যোগ
    app.add_handler(CommandHandler("listsites", list_sites)) # সাইট লিস্ট দেখা
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), content_handler))
    print("Bot with Dynamic Site Adder is running...")
    app.run_polling()
