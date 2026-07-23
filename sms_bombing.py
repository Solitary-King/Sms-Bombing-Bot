import telebot
import requests
import os
import json
import time
import threading
from telebot import types

BOT_TOKEN = '8545503833:AAGtZ_PdZtpjOVezajCJr_B-KztWKyUh16g'
ADMIN_ID = 6535070545
BOT_USERNAME = 'SH_BOMBING_bot'
SUPPORT_USERNAME = '@itsAdminRimon'

bot = telebot.TeleBot(BOT_TOKEN)

# ফাইল ডাটাবেজ
DB_FILE = "bot_users.json"
CONFIG_FILE = "bot_config.json"
REDEEM_FILE = "redeem_codes.json"
SETTINGS_FILE = "bot_settings.json"

# Loader and Saver Functions
def load_db():
    if not os.path.exists(DB_FILE): return {}
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f: return json.load(f)
    except Exception: return {}

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f: json.dump(data, f, indent=4, ensure_ascii=False)

def load_config():
    if not os.path.exists(CONFIG_FILE): return {"unlimited_mode": False, "blacklist": [], "vip_users": []}
    try:
        config = json.load(open(CONFIG_FILE, "r"))
        if "blacklist" not in config: config["blacklist"] = []
        if "vip_users" not in config: config["vip_users"] = []
        return config
    except Exception: return {"unlimited_mode": False, "blacklist": [], "vip_users": []}

def save_config(config):
    with open(CONFIG_FILE, "w") as f: json.dump(config, f)

def load_redeem():
    if not os.path.exists(REDEEM_FILE): return {}
    try:
        with open(REDEEM_FILE, "r", encoding="utf-8") as f: return json.load(f)
    except Exception: return {}

def save_redeem(data):
    with open(REDEEM_FILE, "w", encoding="utf-8") as f: json.dump(data, f, indent=4, ensure_ascii=False)

def load_settings():
    default_settings = {
        "channels": {
            "@solitary_hacker": "https://t.me/solitary_hacker",
            "@S_H_Backup": "https://t.me/S_H_Backup",
            "@DebugStack": "https://t.me/DebugStack"
        },
        "apis": [
            "http://127.0.0.1:5000/api?phone="
        ]
    }
    if not os.path.exists(SETTINGS_FILE):
        save_settings(default_settings)
        return default_settings
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default_settings

def save_settings(data):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# রেজিস্টার ইউজার
def register_user(user_id, first_name, referrer_id=None):
    db = load_db()
    user_id_str = str(user_id)
    if user_id_str not in db:
        db[user_id_str] = {
            "name": first_name, 
            "limit": 3, 
            "referrals": 0, 
            "referred_by": referrer_id, 
            "last_bonus": 0,
            "referral_rewarded": False
        }
        save_db(db)

# রেফার বোনাস দেওয়ার ফাংশন
def give_referral_reward(user_id):
    db = load_db()
    user_id_str = str(user_id)
    
    if user_id_str in db and not db[user_id_str].get("referral_rewarded", False):
        referrer_id = db[user_id_str].get("referred_by")
        if referrer_id and str(referrer_id) in db and str(referrer_id) != user_id_str:
            ref_str = str(referrer_id)
            db[ref_str]["referrals"] += 1
            config = load_config()
            if str(referrer_id) not in config.get("vip_users", []):
                db[ref_str]["limit"] += 2
            try: 
                bot.send_message(int(referrer_id), f"🎉 আপনার রেফারেল লিংকের একজন মেম্বার চ্যানেল জয়েন করে ভেরিফাই করেছে!\n🎁 আপনি পেয়েছেন +২ লিমিট।")
            except Exception: 
                pass
        
        db[user_id_str]["referral_rewarded"] = True
        save_db(db)

def is_user_subscribed_all(user_id):
    settings = load_settings()
    channels = settings.get("channels", {})
    if not channels:
        return True
    for channel in channels.keys():
        try:
            member = bot.get_chat_member(channel, user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False
        except Exception:
            return False
    return True

def main_keyboard(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("ℹ️ Welcome (Profile)"), types.KeyboardButton("💳 Subscription"))
    markup.add(types.KeyboardButton("💣 Bomber"), types.KeyboardButton("🔗 Referral"))
    markup.add(types.KeyboardButton("🎟️ Redeem Code"), types.KeyboardButton("🎁 Daily Bonus"))
    markup.add(types.KeyboardButton("📞 Support"))
    if user_id == ADMIN_ID:
        markup.add(types.KeyboardButton("🚨 Admin Panel 👑"))
    return markup

def get_join_keyboard():
    settings = load_settings()
    channels = settings.get("channels", {})
    join_markup = types.InlineKeyboardMarkup()
    count = 1
    for channel_user, channel_url in channels.items():
        btn = types.InlineKeyboardButton(f"📢 Join Channel {count}", url=channel_url)
        join_markup.add(btn)
        count += 1
    btn_verified = types.InlineKeyboardButton("🔄 Joined All (Check)", callback_data="check_joined")
    join_markup.add(btn_verified)
    return join_markup

def back_inline_markup():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main"))
    return markup

@bot.message_handler(commands=['start'])
def start_command(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    first_name = message.from_user.first_name

    command_text = message.text.split()
    referrer_id = None
    if len(command_text) > 1 and command_text[1].isdigit():
        referrer_id = int(command_text[1])

    register_user(user_id, first_name, referrer_id)

    if is_user_subscribed_all(user_id):
        give_referral_reward(user_id)
        bot.send_message(chat_id, "স্বাগতম! নিচের বাটনগুলো ব্যবহার করে কাজ শুরু করুন।", reply_markup=main_keyboard(user_id))
    else:
        bot.send_message(
            chat_id,
            "⚠️ আমাদের বটের সকল সুবিধা পেতে হলে প্রথমে নিচে দেওয়া **সবগুলো লিংকে** ক্লিক করে আমাদের চ্যানেলগুলোতে জয়েন হতে হবে। জয়েন করার পর 'Joined All (Check)' বাটনে ক্লিক করুন।",
            reply_markup=get_join_keyboard(),
            parse_mode="Markdown"
        )

@bot.callback_query_handler(func=lambda call: call.data == "check_joined")
def check_joined_callback(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id

    if is_user_subscribed_all(user_id):
        give_referral_reward(user_id)
        bot.delete_message(chat_id, call.message.message_id)
        bot.send_message(chat_id, "✅ ধন্যবাদ! আপনার ভেরিফিকেশন সফল হয়েছে। এখন আপনি বট ব্যবহার করতে পারবেন।", reply_markup=main_keyboard(user_id))
    else:
        bot.answer_callback_query(call.id, "❌ আপনি এখনো সবগুলো চ্যানেলে জয়েন করেননি! দয়া করে সবগুলো চ্যানেলে জয়েন করুন।", show_alert=True)

@bot.message_handler(func=lambda message: True)
def handle_menu_buttons(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    text = message.text

    register_user(user_id, message.from_user.first_name)
    db = load_db()
    config = load_config()
    user_data = db.get(str(user_id), {"name": message.from_user.first_name, "limit": 0, "referrals": 0, "last_bonus": 0})

    if not is_user_subscribed_all(user_id):
        bot.send_message(chat_id, "⚠️ দয়া করে আবার সবগুলো চ্যানেলে জয়েন করুন এবং বট ব্যবহার করতে /start লিখুন।", reply_markup=get_join_keyboard())
        return

    is_vip = str(user_id) in config.get("vip_users", [])
    is_unlimited = config.get("unlimited_mode") or is_vip

    if text == "ℹ️ Welcome (Profile)":
        bot.send_message(chat_id, f"🎈 Welcome **{user_data['name']}** to SH BOMBING.\n\nYour User ID: `{user_id}` 🎯", parse_mode="Markdown")

    elif text == "💳 Subscription":
        current_limit = "♾️ Unlimited" if is_unlimited else user_data['limit']
        sub_text = (
            f"👤 **{user_data['name']}**\n🐎 ID: `{user_id}`\n💎 Limit: {current_limit}\n"
            f"🌐 Time: ❌ নেই\n🏅 Total Referrals: {user_data['referrals']}\n\n"
            f"ℹ️ _লিমিট ফুরিয়ে গেলে বা আরো আনলিমিটেড সার্ভিস কিনতে চাইলে নিচে যোগাযোগ করুন:_\n💬 কন্টাক্ট আইডি: {SUPPORT_USERNAME}"
        )
        bot.send_message(chat_id, sub_text, parse_mode="Markdown")

    elif text == "🔗 Referral":
        referral_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
        current_limit = "♾️ Unlimited" if is_unlimited else user_data['limit']
        refer_text = (
            f"🎒 **আপনার রেফারাল লিংক:**\n`{referral_link}`\n\n"
            f"💬 Total Referrals: {user_data['referrals']}\n💎 Limit: {current_limit}\n\n🎁 প্রতি ১টি সফল রেফারের (চ্যানেলে জয়েন হতে হবে) জন্য আপনি পাবেন **+২ টি লিমিট**!"
        )
        bot.send_message(chat_id, refer_text, parse_mode="Markdown")

    elif text == "💣 Bomber":
        if not is_unlimited and user_data['limit'] <= 0:
            bot.send_message(chat_id, f"❌ দুঃখিত! আপনার লিমিট শেষ হয়ে গেছে।\n\n👉 লিমিট বাড়াতে বন্ধুদের রেফার করুন অথবা কন্টাক্ট করুন: {SUPPORT_USERNAME}")
            return
        
        bomber_msg = (
            "💣 SH BOMBING\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "👉 যেই নম্বরে SMS পাঠাবেন, সেই নম্বরটি নিচে লিখে পাঠান (যেমন: 017xxxxxxxx):"
        )
        sent_msg = bot.send_message(chat_id, bomber_msg)
        bot.register_next_step_handler(sent_msg, process_number)

    elif text == "🎟️ Redeem Code":
        sent_msg = bot.send_message(chat_id, "🔑 আপনার রিডিম কোডটি (Redeem Code) এখানে লিখুন:")
        bot.register_next_step_handler(sent_msg, process_claim_redeem)

    elif text == "🎁 Daily Bonus":
        if is_vip:
            bot.send_message(chat_id, "♾️ আপনার অ্যাকাউন্ট ইতিমধ্যে আনলিমিটেড মোডে আছে, বোনাস লিমিটের প্রয়োজন নেই!")
            return
        current_time = time.time()
        last_bonus = user_data.get("last_bonus", 0)
        
        if current_time - last_bonus < 86400:
            remaining = 86400 - (current_time - last_bonus)
            hours = int(remaining // 3600)
            minutes = int((remaining % 3600) // 60)
            bot.send_message(chat_id, f"❌ আপনি ইতিমধ্যে আজকের বোনাস নিয়ে নিয়েছেন! আবার ক্লেইম করতে `{hours}` ঘণ্টা `{minutes}` মিনিট অপেক্ষা করুন।", parse_mode="Markdown")
        else:
            db[str(user_id)]["limit"] += 2
            db[str(user_id)]["last_bonus"] = current_time
            save_db(db)
            bot.send_message(chat_id, f"🎁 **ডেইলি বোনাস সফল!**\n🎉 আপনার অ্যাকাউন্টে **+২টি** লিমিট যুক্ত করা হয়েছে।", parse_mode="Markdown")

    elif text == "📞 Support":
        bot.send_message(chat_id, f"📞 **আমাদের কাস্টমার সাপোর্ট টিম:**\n\nযেকোনো সমস্যা বা লিমিট কিনতে সরাসরি যোগাযোগ করুন:\n💬 ইউজারনেম: {SUPPORT_USERNAME}", parse_mode="Markdown")

    elif text == "🚨 Admin Panel 👑" and chat_id == ADMIN_ID:
        show_admin_panel(chat_id, config, db)
    else:
        bot.send_message(chat_id, "অনুগ্রহ করে নিচের দেওয়া বাটনগুলো ব্যবহার করুন।", reply_markup=main_keyboard(user_id))

def show_admin_panel(chat_id, config, db):
    unlimited_status = "🟢 ON" if config.get("unlimited_mode") else "🔴 OFF"
    settings = load_settings()
    
    admin_menu = (
        f"👑 ══════ **অ্যাডমিন কন্ট্রোল প্যানেল** ══════ 👑\n\n"
        f"👥 মোট একটিভ ইউজার: {len(db)} জন সদস্য\n"
        f"♾️ গ্লোবাল আনলিমিটেড মোড স্ট্যাটাস: {unlimited_status}\n"
        f"📢 মোট যুক্ত চ্যানেল: {len(settings.get('channels', {}))} টি\n"
        f"🌐 মোট একটিভ API: {len(settings.get('apis', []))} টি\n"
        f"🚫 মোট ব্ল্যাকলিস্টেড নাম্বার: {len(config.get('blacklist', []))} টি\n"
        f"💎 নির্দিষ্ট আনলিমিটেড (VIP) ইউজার: {len(config.get('vip_users', []))} জন\n\n"
        f"⚙️ নিচে থেকে আপনার কাঙ্ক্ষিত অপশন সিলেক্ট করুন:"
    )

    admin_markup = types.InlineKeyboardMarkup()
    
    # ২ টি করে বাটন পার রো-তে রাখা হয়েছে নিখুঁত লেআউটের জন্য
    admin_markup.add(
        types.InlineKeyboardButton("📤 Send All Msg", callback_data="admin_send_all"),
        types.InlineKeyboardButton("⚙️ Single Limit", callback_data="admin_edit_limit")
    )
    admin_markup.add(
        types.InlineKeyboardButton("⚙️ All Users Limit", callback_data="admin_edit_all_limit"),
        types.InlineKeyboardButton("💎 VIP Set Mode", callback_data="admin_set_vip")
    )
    admin_markup.add(
        types.InlineKeyboardButton("🎟️ Create Code", callback_data="admin_create_redeem"),
        types.InlineKeyboardButton("📊 Code Status", callback_data="admin_view_redeem")
    )
    admin_markup.add(
        types.InlineKeyboardButton("🚫 Add Blacklist", callback_data="admin_add_blacklist"), 
        types.InlineKeyboardButton("❌ Rem Blacklist", callback_data="admin_rem_blacklist")
    )
    admin_markup.add(
        types.InlineKeyboardButton("📋 View Blacklist", callback_data="admin_view_blacklist")
    )
    
    # চ্যানেল ও এপিআই সম্পর্কিত ৬টি বাটন গ্লোবাল মোডের ঠিক উপরে নিচে আনা হলো
    admin_markup.add(
        types.InlineKeyboardButton("📢 Add Channel", callback_data="admin_add_channel"),
        types.InlineKeyboardButton("❌ Rem Channel", callback_data="admin_rem_channel")
    )
    admin_markup.add(
        types.InlineKeyboardButton("📋 View Channels", callback_data="admin_view_channels"),
        types.InlineKeyboardButton("🌐 Add API", callback_data="admin_add_api")
    )
    admin_markup.add(
        types.InlineKeyboardButton("❌ Rem API", callback_data="admin_rem_api"),
        types.InlineKeyboardButton("📋 View APIs", callback_data="admin_view_apis")
    )
    
    btn_txt = "🔒 Turn OFF Global" if config.get("unlimited_mode") else "🔓 Turn ON Global"
    admin_markup.add(types.InlineKeyboardButton(btn_txt, callback_data="toggle_unlimited"))
    
    bot.send_message(chat_id, admin_menu, reply_markup=admin_markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_") or call.data in ["back_to_main", "toggle_unlimited"])
def admin_callbacks(call):
    chat_id = call.message.chat.id

    if call.data == "back_to_main":
        bot.delete_message(chat_id, call.message.message_id)
        bot.send_message(chat_id, "🏡 আপনি মূল মেনুতে ফিরে এসেছেন।", reply_markup=main_keyboard(chat_id))
        return

    if chat_id != ADMIN_ID: return

    # ব্ল্যাকলিস্ট ভিউ
    if call.data == "admin_view_blacklist":
        config = load_config()
        bl = config.get("blacklist", [])
        msg = "🚫 **ব্ল্যাকলিস্টে থাকা নাম্বার সমূহ:**\n\n"
        if not bl:
            msg += "❌ বর্তমানে কোনো নাম্বার ব্ল্যাকলিস্টে নেই।"
        else:
            for idx, num in enumerate(bl, 1):
                msg += f"{idx}. `{num}`\n"
        bot.send_message(chat_id, msg, reply_markup=back_inline_markup(), parse_mode="Markdown")

    # চ্যানেল ম্যানেজমেন্ট
    elif call.data == "admin_add_channel":
        bot.delete_message(chat_id, call.message.message_id)
        sent_msg = bot.send_message(chat_id, "📢 নতুন চ্যানেল যোগ করতে ফরম্যাটটি পাঠান:\n\n`@username Link`\n\nউদাহরণ:\n`@mychannel https://t.me/mychannel`", parse_mode="Markdown")
        bot.register_next_step_handler(sent_msg, process_add_channel)

    elif call.data == "admin_rem_channel":
        bot.delete_message(chat_id, call.message.message_id)
        settings = load_settings()
        chans = settings.get("channels", {})
        msg = "❌ যে চ্যানেলটি সরাতে চান সেটির **Username** পাঠান (যেমন `@solitary_hacker`):\n\n**বর্তমান চ্যানেল সমুহ:**\n"
        for k in chans.keys(): msg += f"- `{k}`\n"
        sent_msg = bot.send_message(chat_id, msg, parse_mode="Markdown")
        bot.register_next_step_handler(sent_msg, process_rem_channel)

    elif call.data == "admin_view_channels":
        settings = load_settings()
        chans = settings.get("channels", {})
        msg = "📢 **বর্তমান চ্যানেল তালিকা:**\n\n"
        if not chans:
            msg += "❌ বর্তমানে কোনো চ্যানেল যুক্ত নেই।"
        else:
            for idx, (username, link) in enumerate(chans.items(), 1):
                msg += f"{idx}. `{username}` ➔ [Link]({link})\n"
        bot.send_message(chat_id, msg, reply_markup=back_inline_markup(), parse_mode="Markdown", disable_web_page_preview=True)

    # এপিআই ম্যানেজমেন্ট
    elif call.data == "admin_add_api":
        bot.delete_message(chat_id, call.message.message_id)
        sent_msg = bot.send_message(chat_id, "🌐 নতুন API লিঙ্কটি পাঠান:\n(অবশ্যই শেষে `phone=` রাখবেন)\n\nউদাহরণ:\n`http://example.com/api?phone=`", parse_mode="Markdown")
        bot.register_next_step_handler(sent_msg, process_add_api)

    elif call.data == "admin_rem_api":
        bot.delete_message(chat_id, call.message.message_id)
        settings = load_settings()
        apis = settings.get("apis", [])
        msg = "🗑️ যে নম্বর API-টি ডিলিট করতে চান সেই নম্বরটি লিখে পাঠান (যেমন: 1, 2, 3):\n\n"
        for idx, api in enumerate(apis, 1):
            msg += f"{idx}. `{api}`\n"
        sent_msg = bot.send_message(chat_id, msg, parse_mode="Markdown")
        bot.register_next_step_handler(sent_msg, process_rem_api)

    elif call.data == "admin_view_apis":
        settings = load_settings()
        apis = settings.get("apis", [])
        msg = "🌐 **বর্তমান বোম্বিং API তালিকা:**\n\n"
        if not apis:
            msg += "❌ বর্তমানে কোনো API যুক্ত নেই।"
        else:
            for idx, api in enumerate(apis, 1):
                msg += f"{idx}. `{api}`\n"
        bot.send_message(chat_id, msg, reply_markup=back_inline_markup(), parse_mode="Markdown")

    elif call.data == "admin_send_all":
        bot.delete_message(chat_id, call.message.message_id)
        sent_msg = bot.send_message(chat_id, "📢 সব ইউজারের কাছে পাঠানোর জন্য মেসেজটি দিন:")
        bot.register_next_step_handler(sent_msg, send_broadcast)

    elif call.data == "admin_edit_limit":
        bot.delete_message(chat_id, call.message.message_id)
        sent_msg = bot.send_message(chat_id, "👤 ইউজার আইডি এবং লিমিট পরিবর্তন করার সাইন এভাবে লিখে পাঠান:\n`User_ID +সংখ্যা` বা `-সংখ্যা`")
        bot.register_next_step_handler(sent_msg, process_admin_edit_limit)

    elif call.data == "admin_edit_all_limit":
        bot.delete_message(chat_id, call.message.message_id)
        sent_msg = bot.send_message(chat_id, "⚙️ সব ইউজারের লিমিট একসাথে পরিবর্তন করতে কমান্ড পাঠান (+সংখ্যা/-সংখ্যা/সংখ্যা):")
        bot.register_next_step_handler(sent_msg, process_admin_edit_all_limit)

    elif call.data == "admin_create_redeem":
        bot.delete_message(chat_id, call.message.message_id)
        sent_msg = bot.send_message(chat_id, "🎟️ ফরম্যাট: `Code_Name Limit_Amount Max_Uses` (যেমন: FREE50 10 5)")
        bot.register_next_step_handler(sent_msg, process_admin_create_redeem)

    elif call.data == "admin_view_redeem":
        bot.delete_message(chat_id, call.message.message_id)
        sent_msg = bot.send_message(chat_id, "📊 যে রিডিম কোডটির লাইভ স্ট্যাটাস জানতে চান তা লিখে পাঠান:")
        bot.register_next_step_handler(sent_msg, process_admin_view_redeem)

    elif call.data == "admin_add_blacklist":
        bot.delete_message(chat_id, call.message.message_id)
        sent_msg = bot.send_message(chat_id, "🚫 যে নাম্বারটি ব্ল্যাকলিস্ট করতে চান তা দিন (১১ ডিজিট):")
        bot.register_next_step_handler(sent_msg, process_admin_blacklist)

    elif call.data == "admin_rem_blacklist":
        bot.delete_message(chat_id, call.message.message_id)
        sent_msg = bot.send_message(chat_id, "❌ যে নাম্বারটি ব্ল্যাকলিস্ট থেকে সরাতে চান তা দিন:")
        bot.register_next_step_handler(sent_msg, process_admin_rem_blacklist)

    elif call.data == "admin_set_vip":
        bot.delete_message(chat_id, call.message.message_id)
        sent_msg = bot.send_message(chat_id, "💎 ফরম্যাট:\n`User_ID unlimited` অথবা `User_ID normal`")
        bot.register_next_step_handler(sent_msg, process_admin_set_vip)

    elif call.data == "toggle_unlimited":
        config = load_config()
        config["unlimited_mode"] = not config.get("unlimited_mode", False)
        save_config(config)
        bot.answer_callback_query(call.id, f"✅ গ্লোবাল আনলিমিটেড মোড পরিবর্তন করা হয়েছে!", show_alert=True)
        bot.delete_message(chat_id, call.message.message_id)
        db = load_db()
        show_admin_panel(chat_id, config, db)

# চ্যানেল অ্যাড / রিমুভ প্রসেসর
def process_add_channel(message):
    chat_id = message.chat.id
    text = message.text.strip().split()
    if len(text) != 2 or not text[0].startswith("@"):
        bot.send_message(chat_id, "❌ ভুল ফরম্যাট! সঠিক ফরম্যাটে আবার চেষ্টা করুন।", reply_markup=back_inline_markup())
        return
    ch_user, ch_url = text[0], text[1]
    settings = load_settings()
    settings["channels"][ch_user] = ch_url
    save_settings(settings)
    bot.send_message(chat_id, f"✅ চ্যানেল `{ch_user}` সফলভাবে যুক্ত করা হয়েছে!", reply_markup=back_inline_markup(), parse_mode="Markdown")

def process_rem_channel(message):
    chat_id = message.chat.id
    ch_user = message.text.strip()
    settings = load_settings()
    if ch_user in settings.get("channels", {}):
        del settings["channels"][ch_user]
        save_settings(settings)
        bot.send_message(chat_id, f"✅ চ্যানেল `{ch_user}` সরিয়ে নেওয়া হয়েছে!", reply_markup=back_inline_markup(), parse_mode="Markdown")
    else:
        bot.send_message(chat_id, "❌ চ্যানেলটি পাওয়া যায়নি!", reply_markup=back_inline_markup())

# এপিআই অ্যাড / রিমুভ প্রসেসর
def process_add_api(message):
    chat_id = message.chat.id
    api_url = message.text.strip()
    if not api_url.startswith("http"):
        bot.send_message(chat_id, "❌ সঠিক URL প্রদান করুন!", reply_markup=back_inline_markup())
        return
    settings = load_settings()
    settings["apis"].append(api_url)
    save_settings(settings)
    bot.send_message(chat_id, f"✅ নতুন API সফলভাবে যুক্ত করা হয়েছে!", reply_markup=back_inline_markup())

def process_rem_api(message):
    chat_id = message.chat.id
    idx_str = message.text.strip()
    if not idx_str.isdigit():
        bot.send_message(chat_id, "❌ সঠিক নম্বর লিখুন!", reply_markup=back_inline_markup())
        return
    idx = int(idx_str) - 1
    settings = load_settings()
    apis = settings.get("apis", [])
    if 0 <= idx < len(apis):
        removed = apis.pop(idx)
        settings["apis"] = apis
        save_settings(settings)
        bot.send_message(chat_id, f"✅ API রিমুভ করা হয়েছে:\n`{removed}`", reply_markup=back_inline_markup(), parse_mode="Markdown")
    else:
        bot.send_message(chat_id, "❌ ভুল নম্বর বেছে নিয়েছেন!", reply_markup=back_inline_markup())

def send_broadcast(message):
    admin_chat_id = message.chat.id
    db = load_db()
    bot.send_message(admin_chat_id, f"⏳ মোট {len(db)} জন ইউজারের কাছে মেসেজ পাঠানো শুরু হচ্ছে...")
    success, fail = 0, 0
    for user_id in db.keys():
        try:
            bot.copy_message(chat_id=int(user_id), from_chat_id=admin_chat_id, message_id=message.message_id)
            success += 1
        except Exception: fail += 1
    bot.send_message(admin_chat_id, f"📢 ব্রডকাস্ট সম্পন্ন!\n\n✅ সফল: {success} জন\n❌ ব্যর্থ: {fail} জন", reply_markup=back_inline_markup())

def process_admin_edit_limit(message):
    chat_id = message.chat.id
    text = message.text.strip().split()
    if len(text) != 2 or not text[0].isdigit():
        bot.send_message(chat_id, "❌ ভুল ফরম্যাট!", reply_markup=back_inline_markup())
        return
    db = load_db()
    target_id = text[0]
    value_str = text[1]
    if target_id not in db:
        bot.send_message(chat_id, "❌ আইডি পাওয়া যায়নি।", reply_markup=back_inline_markup())
        return
    current_limit = db[target_id].get("limit", 0)
    try:
        if value_str.startswith("+"): new_limit = current_limit + int(value_str[1:])
        elif value_str.startswith("-"): new_limit = max(0, current_limit - int(value_str[1:]))
        else: new_limit = int(value_str)
        db[target_id]["limit"] = new_limit
        save_db(db)
        try: bot.send_message(int(target_id), f"📊 অ্যাডমিন আপনার লিমিট **{new_limit}** করেছে!")
        except: pass
        bot.send_message(chat_id, f"✅ সফল! বর্তমান লিমিট: {new_limit}", reply_markup=back_inline_markup())
    except: bot.send_message(chat_id, "❌ ভুল হয়েছে।", reply_markup=back_inline_markup())

def process_admin_edit_all_limit(message):
    chat_id = message.chat.id
    value_str = message.text.strip()
    db = load_db()
    if not db:
        bot.send_message(chat_id, "❌ ডাটাবেজে কোনো ইউজার নেই!", reply_markup=back_inline_markup())
        return
    success_count = 0
    try:
        if value_str.startswith("+"):
            amount = int(value_str[1:])
            for uid in db.keys():
                db[uid]["limit"] += amount
                success_count += 1
            msg = f"✅ সফলভাবে সব ({success_count}) ইউজারের লিমিট **+{amount}** করে বাড়ানো হয়েছে!"
        elif value_str.startswith("-"):
            amount = int(value_str[1:])
            for uid in db.keys():
                db[uid]["limit"] = max(0, db[uid]["limit"] - amount)
                success_count += 1
            msg = f"✅ সফলভাবে সব ({success_count}) ইউজারের লিমিট **-{amount}** করে কমানো হয়েছে!"
        elif value_str.isdigit():
            amount = int(value_str)
            for uid in db.keys():
                db[uid]["limit"] = amount
                success_count += 1
            msg = f"✅ সফলভাবে সব ({success_count}) ইউজারের লিমিট সরাসরি **{amount}** এ ফিক্সড করা হয়েছে!"
        else:
            bot.send_message(chat_id, "❌ ভুল কমান্ড ফরম্যাট!", reply_markup=back_inline_markup())
            return
        save_db(db)
        bot.send_message(chat_id, msg, reply_markup=back_inline_markup())
    except Exception: bot.send_message(chat_id, "❌ সমস্যা হয়েছে।", reply_markup=back_inline_markup())

def process_admin_create_redeem(message):
    chat_id = message.chat.id
    text = message.text.strip().split()
    if len(text) != 3 or not text[1].isdigit() or not text[2].isdigit():
        bot.send_message(chat_id, "❌ ভুল ফরম্যাট!", reply_markup=back_inline_markup())
        return
    code_name = text[0].upper()
    limit_amount = int(text[1])
    max_uses = int(text[2])
    redeem_db = load_redeem()
    redeem_db[code_name] = {"limit": limit_amount, "max_uses": max_uses, "current_uses": 0, "used_by": []}
    save_redeem(redeem_db)
    bot.send_message(chat_id, f"🎟️ কোড `{code_name}` তৈরি সফল!", reply_markup=back_inline_markup())

def process_admin_view_redeem(message):
    chat_id = message.chat.id
    code_input = message.text.strip().upper()
    redeem_db = load_redeem()

    if code_input not in redeem_db:
        bot.send_message(chat_id, "❌ এই রিডিম কোডটি ডাটাবেজে পাওয়া যায়নি!", reply_markup=back_inline_markup())
        return

    code_data = redeem_db[code_input]
    current_uses = code_data.get("current_uses", 0)
    max_uses = code_data.get("max_uses", 0)
    remaining_uses = max(0, max_uses - current_uses)
    
    status = "🔴 এক্সপায়ার্ড/শেষ হয়ে গেছে" if current_uses >= max_uses else "🟢 সচল (Active)"

    info_msg = (
        f"📊 **রিডিম কোড স্ট্যাটাস:** `{code_input}`\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💎 প্রতি কোডে লিমিট: {code_data.get('limit', 0)} টি\n"
        f"👥 ব্যবহার করেছে: `{current_uses}` জন\n"
        f"⏳ বাকি আছে: `{remaining_uses}` জন ব্যবহার করতে পারবে\n"
        f"🎯 সর্বোচ্চ সীমা: `{max_uses}` জন\n"
        f"🚨 বর্তমান অবস্থা: **{status}**\n\n"
        f"👥 _ব্যবহারকারীদের আইডি তালিকা:_\n`{', '.join(code_data.get('used_by', [])) if code_data.get('used_by') else 'কেউ ব্যবহার করেনি'}`"
    )
    bot.send_message(chat_id, info_msg, reply_markup=back_inline_markup(), parse_mode="Markdown")

def process_admin_blacklist(message):
    chat_id = message.chat.id
    target_num = message.text.strip()
    if not target_num.isdigit() or len(target_num) < 10:
        bot.send_message(chat_id, "❌ সঠিক নাম্বার দিন।", reply_markup=back_inline_markup())
        return
    config = load_config()
    if target_num not in config["blacklist"]:
        config["blacklist"].append(target_num)
        save_config(config)
    bot.send_message(chat_id, f"✅ নাম্বার `{target_num}` ব্ল্যাকলিস্ট করা হয়েছে।", reply_markup=back_inline_markup())

def process_admin_rem_blacklist(message):
    chat_id = message.chat.id
    target_num = message.text.strip()
    config = load_config()
    if target_num in config.get("blacklist", []):
        config["blacklist"].remove(target_num)
        save_config(config)
        bot.send_message(chat_id, f"✅ সফলভাবে `{target_num}` নাম্বারটি ব্ল্যাকলিস্ট থেকে সরানো হয়েছে।", reply_markup=back_inline_markup())
    else:
        bot.send_message(chat_id, "❌ এই নাম্বারটি তালিকায় নেই।", reply_markup=back_inline_markup())

def process_admin_set_vip(message):
    chat_id = message.chat.id
    text = message.text.strip().split()
    if len(text) != 2 or not text[0].isdigit():
        bot.send_message(chat_id, "❌ ভুল ফরম্যাট!", reply_markup=back_inline_markup())
        return
    target_uid = text[0]
    mode = text[1].lower()
    config = load_config()
    db = load_db()
    if target_uid not in db:
        bot.send_message(chat_id, "❌ আইডি ডাটাবেজে নেই।", reply_markup=back_inline_markup())
        return
    if mode == "unlimited":
        if target_uid not in config["vip_users"]: config["vip_users"].append(target_uid)
        save_config(config)
        try: bot.send_message(int(target_uid), "🎉 আপনার অ্যাকাউন্টটি Lifetime Unlimited করা হয়েছে।")
        except: pass
        bot.send_message(chat_id, f"✅ ইউজার `{target_uid}` আনলিমিটেড করা হয়েছে।", reply_markup=back_inline_markup())
    elif mode == "normal":
        if target_uid in config["vip_users"]: config["vip_users"].remove(target_uid)
        save_config(config)
        try: bot.send_message(int(target_uid), "📊 আপনার অ্যাকাউন্টটি সাধারণ মোডে ফিরিয়ে আনা হয়েছে।")
        except: pass
        bot.send_message(chat_id, f"✅ ইউজার `{target_uid}` নরমাল করা হয়েছে।", reply_markup=back_inline_markup())

def process_claim_redeem(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    user_id_str = str(user_id)
    code_input = message.text.strip().upper()
    redeem_db = load_redeem()
    if code_input not in redeem_db:
        bot.send_message(chat_id, "❌ রিডিম কোডটি সঠিক নয়।", reply_markup=back_inline_markup())
        return
    code_data = redeem_db[code_input]
    if user_id_str in code_data.get("used_by", []):
        bot.send_message(chat_id, "❌ আপনি ইতিমধ্যে এই কোডটি ব্যবহার করেছেন!", reply_markup=back_inline_markup())
        return
    if code_data["current_uses"] >= code_data["max_uses"]:
        bot.send_message(chat_id, "❌ এই কোডের সীমা শেষ!", reply_markup=back_inline_markup())
        return
    db = load_db()
    bonus_limit = code_data["limit"]
    db[user_id_str]["limit"] += bonus_limit
    save_db(db)
    redeem_db[code_input]["current_uses"] += 1
    redeem_db[code_input]["used_by"].append(user_id_str)
    save_redeem(redeem_db)
    bot.send_message(chat_id, f"🎉 আপনি পেয়েছেন **+{bonus_limit}** লিমিট!", reply_markup=back_inline_markup())

def background_bombing(target_number):
    settings = load_settings()
    api_list = settings.get("apis", [])
    for api_url in api_list:
        try: requests.get(f"{api_url}{target_number}", timeout=8)
        except: continue

def process_number(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    target_number = message.text.strip()
    db = load_db()
    config = load_config()
    user_data = db.get(str(user_id), {"limit": 0})

    if target_number == '/start':
        start_command(message)
        return
    if target_number in ["ℹ️ Welcome (Profile)", "💳 Subscription", "💣 Bomber", "🔗 Referral", "🎟️ Redeem Code", "🎁 Daily Bonus", "📞 Support", "🚨 Admin Panel 👑"]:
        bot.send_message(chat_id, "অনুরোধ বাতিল করা হয়েছে।", reply_markup=main_keyboard(user_id))
        return
    if not target_number.isdigit():
        bot.send_message(chat_id, "❌ অনুগ্রহ করে সঠিক মোবাইল নাম্বার লিখুন।", reply_markup=main_keyboard(user_id))
        return
    if target_number in config.get("blacklist", []):
        bot.send_message(chat_id, "🚫 দুঃখিত! এই নাম্বারে অ্যাটাক করা অ্যাডমিন কর্তৃক নিষিদ্ধ।", reply_markup=back_inline_markup())
        return

    is_unlimited = config.get("unlimited_mode") or (str(user_id) in config.get("vip_users", []))
    if not is_unlimited and user_data['limit'] <= 0:
        bot.send_message(chat_id, f"❌ আপনার কোনো লিমিট অবশিষ্ট নেই।", reply_markup=back_inline_markup())
        return

    if not is_unlimited:
        db[str(user_id)]["limit"] -= 1
        save_db(db)
        rem = f"📉 আপনার লিমিট থেকে ১ লিমিট কাটা হয়েছে। অবশিষ্ট লিমিট: {db[str(user_id)]['limit']}"
    else: rem = "♾️ আনলিমিটেড মোড সক্রিয় রয়েছে!"

    threading.Thread(target=background_bombing, args=(target_number,), daemon=True).start()
    bot.send_message(chat_id, f"✅ আপনার রিকোয়েস্ট সফল হয়েছে!\n\n{rem}", reply_markup=back_inline_markup())

print("বট চালুর প্রস্তুত...")
bot.infinity_polling()
