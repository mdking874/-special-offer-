import telebot
import requests
from bs4 import BeautifulSoup
import random
import json
import time
import os
import re 
from datetime import datetime, timedelta

# ---------------------------------------------------------
# ১. কনফিগারেশন
BOT_TOKEN = "8195990732:AAGdnFVAbqlOiSIELOWHk7ArS1gm80AFDLY"
ADMIN_ID = 1933498659  # আপনার Numerical ID দিন

# ২. ভিডিও সাইট লিস্ট
REGULAR_SITES = [
    "https://fry99.cc/latest-videos/",
    "https://desibf.com/tag/desi-49/",
    "https://www.desitales2.com/videos/tag/desi49/",
    "https://www.desitales2.com/videos/category/bangla-sex/"
]
LIVE_SITES = ["https://desibf.com/live/", "https://www.desitales2.com/live-cams/"]

# ৩. ক্লিন প্লেয়ার বেস ইউআরএল
CLEAN_PLAYER_URL = "https://hlsjs.video-dev.org/demo/?src="
# ---------------------------------------------------------

bot = telebot.TeleBot(BOT_TOKEN)

# ফাইল ডাটাবেস
USER_DATA_FILE = "users_db.json"
KEYS_FILE = "keys_db.json"
DEFAULT_THUMB = "https://cdn-icons-png.flaticon.com/512/12560/12560376.png"

def load_db(file):
    if not os.path.exists(file): return {}
    try:
        with open(file, "r") as f: return json.load(f)
    except: return {}

def save_db(file, data):
    with open(file, "w") as f: json.dump(data, f, indent=4)

def is_subscribed(user_id):
    users = load_db(USER_DATA_FILE)
    uid = str(user_id)
    if uid in users:
        expiry = datetime.strptime(users[uid], "%Y-%m-%d %H:%M:%S")
        if expiry > datetime.now(): return True, users[uid]
    return False, None

# --- অ্যাডভান্সড লিংক এক্সট্র্যাক্টর ---
def get_clean_stream(page_url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(page_url, headers=headers, timeout=10)
        html = response.text
        
        # .m3u8 খোঁজা (সবচেয়ে কার্যকর)
        m3u8_links = re.findall(r'(https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*)', html)
        if m3u8_links:
            return CLEAN_PLAYER_URL + m3u8_links[0]
            
        # .mp4 খোঁজা
        mp4_links = re.findall(r'(https?://[^\s"\'<>]+\.mp4)', html)
        if mp4_links:
            return mp4_links[0]
            
        return None
    except: return None

# --- উন্নত স্ক্র্যাপার (সার্চ অপশনসহ) ---
def scrape_videos(search_query=None, is_live=False):
    target_list = LIVE_SITES if is_live else REGULAR_SITES
    results = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    for site in target_list:
        try:
            res = requests.get(site, headers=headers, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            for a_tag in soup.find_all('a'):
                img = a_tag.find('img')
                if img and a_tag.get('href'):
                    title = (img.get('alt') or img.get('title') or "Hot Video").lower()
                    video_page = a_tag.get('href')
                    
                    if not video_page.startswith("http"):
                        video_page = "/".join(site.split("/")[:3]) + video_page
                    
                    # সার্চ কুয়েরি থাকলে ফিল্টার করবে
                    if search_query and search_query.lower() not in title:
                        continue
                        
                    thumb = img.get('src') or img.get('data-src')
                    if thumb and not thumb.startswith("http"): thumb = "https:" + thumb
                    
                    results.append({'title': title.capitalize(), 'url': video_page, 'thumb': thumb})
        except: continue
    return results

# --- কমান্ড হ্যান্ডলার ---

@bot.message_handler(commands=['start'])
def start(message):
    sub, exp = is_subscribed(message.chat.id)
    if sub:
        bot.reply_to(message, f"✅ আপনি প্রিমিয়াম মেম্বার।\n⏳ মেয়াদ: {exp}\n\nভিডিও পেতে নাম লিখে সার্চ করুন অথবা 'video'/'live' লিখুন।")
    else:
        bot.reply_to(message, f"🚫 সাবস্ক্রিপশন নেই!\nকি (Key) কিনতে অ্যাডমিনকে মেসেজ দিন।\n👤 অ্যাডমিন: [Contact](tg://user?id={ADMIN_ID})\n\nরিডিম করতে: `/redeem YOUR_KEY`", parse_mode='Markdown')

@bot.message_handler(commands=['gen'])
def gen_key(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        _, days, slots = message.text.split()
        key = f"VIP-{random.randint(100,999)}-{random.randint(100,999)}"
        keys = load_db(KEYS_FILE)
        keys[key] = {"days": int(days), "slots": int(slots)}
        save_db(KEYS_FILE, keys)
        bot.reply_to(message, f"🔑 Key: `{key}`\n⏳ Days: {days}\n👥 Slots: {slots}")
    except: bot.reply_to(message, "ইউজ: `/gen দিন স্লট` (যেমন: /gen 30 5)")

@bot.message_handler(commands=['redeem'])
def redeem(message):
    try:
        key_input = message.text.split()[1]
        keys = load_db(KEYS_FILE)
        if key_input in keys:
            users = load_db(USER_DATA_FILE)
            exp = datetime.now() + timedelta(days=keys[key_input]['days'])
            users[str(message.chat.id)] = exp.strftime("%Y-%m-%d %H:%M:%S")
            save_db(USER_DATA_FILE, users)
            
            keys[key_input]['slots'] -= 1
            if keys[key_input]['slots'] <= 0: del keys[key_input]
            save_db(KEYS_FILE, keys)
            bot.reply_to(message, "🎉 প্রিমিয়াম অ্যাক্টিভেট হয়েছে!")
        else: bot.reply_to(message, "❌ ভুল বা মেয়াদী কি।")
    except: bot.reply_to(message, "ইউজ: `/redeem KEY`")

# --- মূল লজিক (সার্চ এবং ক্লিন ভিডিও) ---
@bot.message_handler(func=lambda m: True)
def handle_text(message):
    uid = message.chat.id
    sub, _ = is_subscribed(uid)
    if not sub:
        bot.send_message(uid, "🚫 আগে সাবস্ক্রিপশন নিন।")
        return

    query = message.text.lower()
    is_live = "live" in query
    
    bot.send_message(uid, "🔍 ভিডিও খোঁজা হচ্ছে, দয়া করে অপেক্ষা করুন...")
    
    # ১. স্ক্র্যাপ করে সম্ভাব্য ভিডিওর লিস্ট নেওয়া
    search_term = None if query in ["video", "live"] else query
    videos = scrape_videos(search_query=search_term, is_live=is_live)
    
    if not videos:
        bot.send_message(uid, "❌ দুঃখিত, আপনার সার্চ অনুযায়ী কোনো ভিডিও পাওয়া যায়নি।")
        return

    random.shuffle(videos)
    found_video = False

    # ২. ভিডিওর লিস্ট থেকে ক্লিন লিংক চেক করা (সর্বোচ্চ ১০টি চেক করবে)
    for v in videos[:10]:
        clean_link = get_clean_stream(v['url'])
        if clean_link:
            caption = f"🎬 **{v['title']}**\n🛡️ Status: Ad-Free Player ✅\n\n▶️ [Watch Video Now]({clean_link})"
            thumb = v['thumb'] if v['thumb'] else DEFAULT_THUMB
            try:
                bot.send_photo(uid, thumb, caption=caption, parse_mode='Markdown')
                found_video = True
                break # ভিডিও পাওয়া গেলে লুপ বন্ধ
            except:
                bot.send_message(uid, caption, parse_mode='Markdown')
                found_video = True
                break
    
    if not found_video:
        bot.send_message(uid, "⚠️ এই মুহূর্তে কোনো ডাইরেক্ট প্লেয়ার লিংক পাওয়া যায়নি। অন্য কিছু লিখে সার্চ করুন।")

print("Universal Search & Clean Player Bot Started...")
bot.infinity_polling()
