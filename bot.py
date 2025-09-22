import os
import logging
import asyncio
import threading
import signal
import sys
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dotenv import load_dotenv
from flask import Flask, request
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputFile,
    ChatMember,
    ChatMemberUpdated,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    ChatMemberHandler,
    MessageHandler,
    filters,
)
from telegram.error import InvalidToken, BadRequest
from telegram.constants import ChatMemberStatus

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Global bot application instance
bot_app = None

# Global variables for bot functionality
user_activity = {}  # Track user activity
auto_posts = []  # Store auto-post content
last_auto_post_time = None
group_settings = {}  # Store group-specific settings
admin_users = set()  # Store admin user IDs

# Default auto-post messages (you can customize these)
DEFAULT_AUTO_POSTS = [
    "🚀 **TrustCoin Update!** 🚀\n\n💎 Don't forget to claim your daily mining rewards!\n⛏️ Start your 24-hour mining session now!\n\n📱 Download the app: https://www.trust-coin.site",
    "🎁 **Daily Reminder!** 🎁\n\n🌟 Complete your missions for extra points!\n🎰 Spin the Lucky Wheel for bonus rewards!\n\n💰 1,000 points = 1 TBN token!",
    "👥 **Community Update!** 👥\n\n🔗 Invite friends and earn 1,000 points per referral!\n🏆 Climb the leaderboards and win prizes!\n\n✨ Join our growing TrustCoin family!",
    "📈 **TrustCoin News!** 📈\n\n🔥 Deflationary tokenomics in action!\n🏛️ Governance features coming soon!\n\n🌐 Follow us on all social platforms!",
    "⚡ **Mining Tip!** ⚡\n\n💡 Keep your mining sessions active for maximum rewards!\n📊 Track your progress in the app!\n\n🎯 Complete missions for bonus points!"
]

# Signal handler for graceful shutdown
def signal_handler(sig, frame):
    """Handle shutdown signals gracefully."""
    logger.info("🛑 Received shutdown signal. Stopping bot gracefully...")
    if bot_app:
        try:
            # Create health status file for Docker
            with open('/tmp/bot_healthy', 'w') as f:
                f.write('stopping')
        except:
            pass
    sys.exit(0)

# Register signal handlers only in main thread
try:
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
except ValueError:
    # Not in main thread, skip signal handlers
    pass

# Get bot token from environment variables
BOT_TOKEN_ENG = os.getenv('BOT_TOKEN_ENG')
ADMIN_USER_IDS = os.getenv('ADMIN_USER_IDS', '').split(',')  # Comma-separated admin user IDs
AUTO_POST_INTERVAL = int(os.getenv('AUTO_POST_INTERVAL', '120'))  # Default 2 minutes (120 seconds)

# Validate that the bot token is loaded
if not BOT_TOKEN_ENG:
    raise ValueError("❌ BOT_TOKEN_ENG not found in environment variables. Please check your .env file.")

# Initialize admin users
for admin_id in ADMIN_USER_IDS:
    if admin_id.strip():
        admin_users.add(int(admin_id.strip()))

# Initialize auto posts
auto_posts = DEFAULT_AUTO_POSTS.copy()

# Main menu keyboard
def build_main_menu() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("📋 Overview & Getting Started", callback_data="overview")],
        [InlineKeyboardButton("⛏️ Mining & Points", callback_data="points")],
        [InlineKeyboardButton("🎯 Missions & Rewards", callback_data="missions")],
        [InlineKeyboardButton("👥 Referral & Community", callback_data="referral")],
        [InlineKeyboardButton("📈 Tokenomics & Roadmap", callback_data="roadmap")],
        [InlineKeyboardButton("📱 Download App", callback_data="download")],
        [InlineKeyboardButton("🔒 Security & Anti-Cheat", callback_data="security")],
        [InlineKeyboardButton("❓ FAQ", callback_data="faq")],
        [InlineKeyboardButton("🌐 Social Links", callback_data="social")],
        [InlineKeyboardButton("🌍 Language Groups", callback_data="language_groups")],
    ]
    return InlineKeyboardMarkup(keyboard)

# Helper functions for group management and user tracking

def is_admin(user_id: int) -> bool:
    """Check if user is an admin."""
    return user_id in admin_users

def track_user_activity(user_id: int, username: str = None, activity_type: str = "message"):
    """Track user activity for monitoring."""
    current_time = datetime.now()
    if user_id not in user_activity:
        user_activity[user_id] = {
            'username': username,
            'first_seen': current_time,
            'last_activity': current_time,
            'message_count': 0,
            'activity_types': []
        }
    
    user_activity[user_id]['last_activity'] = current_time
    user_activity[user_id]['username'] = username or user_activity[user_id].get('username')
    
    if activity_type == "message":
        user_activity[user_id]['message_count'] += 1
    
    if activity_type not in user_activity[user_id]['activity_types']:
        user_activity[user_id]['activity_types'].append(activity_type)

async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send welcome message to new group members."""
    new_member = update.chat_member.new_chat_member.user
    chat_title = update.effective_chat.title or "this group"
    chat_id = update.effective_chat.id
    
    logging.info(f"New member joined - Chat ID: {chat_id}, User: {new_member.first_name} ({new_member.id})")
    
    welcome_message = (
        f"🎉 Welcome to {chat_title}, {new_member.first_name}!\n\n"
        f"🚀 **TrustCoin Community** welcomes you!\n\n"
        f"💎 Ready to start mining? Type /start to explore all features!\n"
        f"📱 Download our app: https://www.trust-coin.site\n\n"
        f"🎁 **New users get 1,000 points bonus!**"
    )
    
    try:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=welcome_message,
            parse_mode="Markdown"
        )
        logging.info(f"Welcome message sent to {new_member.first_name} in {chat_title}")
    except Exception as e:
        logging.error(f"Error sending welcome message: {e}")

async def handle_chat_member_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle chat member updates (joins, leaves, etc.)."""
    logging.info(f"🔔 Chat member update received: {update.chat_member}")
    
    result = extract_status_change(update.chat_member)
    if result is None:
        logging.info("No status change detected")
        return

    was_member, is_member = result
    cause_name = update.chat_member.from_user.mention_html()
    member_name = update.chat_member.new_chat_member.user.mention_html()
    
    logging.info(f"Member status change - Was member: {was_member}, Is member: {is_member}")

    if not was_member and is_member:
        # New member joined
        logging.info(f"New member joined: {member_name}")
        await welcome_new_member(update, context)
    elif was_member and not is_member:
        # Member left
        user_id = update.chat_member.new_chat_member.user.id
        if user_id in user_activity:
            track_user_activity(user_id, update.chat_member.new_chat_member.user.username, "left_group")
        logging.info(f"Member left: {member_name}")

def extract_status_change(chat_member_update: ChatMemberUpdated) -> Optional[tuple[bool, bool]]:
    """Extract whether the user was a member before and after the update."""
    status_change = chat_member_update.difference().get("status")
    old_is_member, new_is_member = chat_member_update.difference().get("is_member", (None, None))

    if status_change is None:
        return None

    old_status, new_status = status_change
    was_member = old_status in [
        ChatMemberStatus.MEMBER,
        ChatMemberStatus.OWNER,
        ChatMemberStatus.ADMINISTRATOR,
    ] or (old_status == ChatMemberStatus.RESTRICTED and old_is_member is True)
    
    is_member = new_status in [
        ChatMemberStatus.MEMBER,
        ChatMemberStatus.OWNER,
        ChatMemberStatus.ADMINISTRATOR,
    ] or (new_status == ChatMemberStatus.RESTRICTED and new_is_member is True)

    return was_member, is_member

async def auto_post_to_groups():
    """Send auto posts to configured groups."""
    global last_auto_post_time, bot_app
    
    if not auto_posts or not bot_app:
        logging.warning("No auto posts or bot app available")
        return
    
    # Select a random post from the list
    post_content = random.choice(auto_posts)
    
    # Get all groups where the bot is active
    group_chat_ids = os.getenv('GROUP_CHAT_IDS', '').split(',')
    
    if not group_chat_ids or not group_chat_ids[0].strip():
        logging.warning("No group chat IDs configured in GROUP_CHAT_IDS")
        return
    
    posts_sent = 0
    for chat_id in group_chat_ids:
        if chat_id.strip():
            try:
                await bot_app.bot.send_message(
                    chat_id=int(chat_id.strip()),
                    text=post_content,
                    parse_mode="Markdown"
                )
                posts_sent += 1
                logging.info(f"📢 Auto-posted to group {chat_id}")
                await asyncio.sleep(1)  # Small delay between posts
            except Exception as e:
                logging.error(f"❌ Error auto-posting to group {chat_id}: {e}")
    
    last_auto_post_time = datetime.now()
    logging.info(f"✅ Auto-posting completed - sent to {posts_sent} groups")

async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle messages in group chats for user interaction and monitoring."""
    if not update.message or not update.effective_user:
        logging.info("No message or user in group message handler")
        return
    
    user_id = update.effective_user.id
    username = update.effective_user.username
    message_text = update.message.text or ""
    chat_id = update.effective_chat.id
    
    logging.info(f"📨 Group message received - Chat ID: {chat_id}, User: {user_id}, Message: {message_text[:50]}...")
    
    # Track user activity
    track_user_activity(user_id, username, "message")
    
    # Smart responses to greetings and keywords
    if any(word in message_text.lower() for word in ["hello", "hi", "مرحبا", "السلام عليكم", "hallo", "привет", "здравствуйте", "bonjour", "नमस्ते", "merhaba", "selam"]):
        responses = [
            "🚀 Welcome to TrustCoin community! Ready to start mining? Type /start for full info!",
            "💎 Hello! Join thousands of miners earning TBN tokens daily! /start to begin",
            "🎁 Hi there! Get your 1,000 points welcome bonus - download our app now!",
            "⛏️ Greetings, future miner! Start your 24-hour mining session today!"
        ]
        try:
            await update.message.reply_text(random.choice(responses))
            logging.info(f"✅ Replied to greeting in group {chat_id}")
        except Exception as e:
            logging.error(f"❌ Error replying to greeting: {e}")
    
    # Respond to mining-related keywords
    elif any(word in message_text.lower() for word in ["mining", "mine", "تعدين", "نقاط", "points", "earn", "كسب"]):
        try:
            await update.message.reply_text("⛏️ **Mining Info:** Earn up to 1,000 points every 24 hours! 💰 1,000 points = 1 TBN token. Download the app and start mining now! 📱")
            logging.info(f"✅ Replied to mining query in group {chat_id}")
        except Exception as e:
            logging.error(f"❌ Error replying to mining query: {e}")
    
    # Respond to app/download keywords  
    elif any(word in message_text.lower() for word in ["app", "download", "تحميل", "تطبيق", "link", "رابط"]):
        try:
            await update.message.reply_text("📱 **Download TrustCoin App:**\n🤖 Android: https://play.google.com/store/apps/details?id=com.jawad06_dev.trustcoinmobile.v3\n🌐 Website: https://www.trust-coin.site")
            logging.info(f"✅ Replied to download query in group {chat_id}")
        except Exception as e:
            logging.error(f"❌ Error replying to download query: {e}")
    
    # Respond to certain keywords or mentions
    bot_username = context.bot.username
    if bot_username and f"@{bot_username}" in message_text.lower():
        response_messages = [
            "🚀 Hello! I'm here to help with TrustCoin! Type /start to see all features!",
            "💎 Need help with mining? Download our app and start earning points!",
            "🎯 Want to learn about missions and rewards? Use /start to explore!",
            "👥 Looking to join our community? Check out our social links with /start!",
            "📱 Ready to start mining? Get the app at https://www.trust-coin.site"
        ]
        
        try:
            await update.message.reply_text(
                random.choice(response_messages),
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Error responding to mention: {e}")
    
    # Respond to common keywords
    keywords_responses = {
        "mining": "⛏️ Start your 24-hour mining session in the TrustCoin app! Earn up to 1,000 points daily!",
        "points": "💰 Earn points through mining, missions, and referrals! 1,000 points = 1 TBN token!",
        "app": "📱 Download the TrustCoin app: https://www.trust-coin.site",
        "referral": "🔗 Invite friends and earn 1,000 points per successful referral!",
        "token": "💎 TBN tokens will be available after mainnet launch on Binance Smart Chain!",
        "help": "❓ Type /start to see all available information and features!"
    }
    
    for keyword, response in keywords_responses.items():
        if keyword in message_text.lower() and random.random() < 0.3:  # 30% chance to respond
            try:
                await update.message.reply_text(response, parse_mode="Markdown")
                break
            except Exception as e:
                logger.error(f"Error responding to keyword {keyword}: {e}")

# Admin commands

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show bot statistics (admin only)."""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ You don't have permission to use this command.")
        return
    
    total_users = len(user_activity)
    active_users_24h = sum(1 for user in user_activity.values() 
                          if datetime.now() - user['last_activity'] <= timedelta(hours=24))
    total_messages = sum(user.get('message_count', 0) for user in user_activity.values())
    
    stats_text = (
        f"📊 **Bot Statistics**\n\n"
        f"👥 **Total Users Tracked:** {total_users}\n"
        f"🟢 **Active Users (24h):** {active_users_24h}\n"
        f"💬 **Total Messages:** {total_messages}\n"
        f"📝 **Auto Posts Available:** {len(auto_posts)}\n"
        f"⏰ **Auto Post Interval:** {AUTO_POST_INTERVAL} seconds\n"
        f"🔧 **Admin Users:** {len(admin_users)}"
    )
    
    await update.message.reply_text(stats_text, parse_mode="Markdown")

async def admin_add_post(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add a new auto post (admin only)."""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ You don't have permission to use this command.")
        return
    
    if not context.args:
        await update.message.reply_text(
            "📝 **Usage:** /addpost <message>\n\n"
            "**Example:** /addpost 🚀 New TrustCoin update! Check out our latest features!"
        )
        return
    
    new_post = " ".join(context.args)
    auto_posts.append(new_post)
    
    await update.message.reply_text(
        f"✅ **Auto post added successfully!**\n\n"
        f"📝 **Post:** {new_post}\n"
        f"📊 **Total posts:** {len(auto_posts)}"
    )

async def admin_list_posts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all auto posts (admin only)."""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ You don't have permission to use this command.")
        return
    
    if not auto_posts:
        await update.message.reply_text("📝 No auto posts configured.")
        return
    
    posts_text = "📝 **Auto Posts:**\n\n"
    for i, post in enumerate(auto_posts, 1):
        posts_text += f"**{i}.** {post[:100]}{'...' if len(post) > 100 else ''}\n\n"
    
    await update.message.reply_text(posts_text, parse_mode="Markdown")

async def admin_remove_post(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Remove an auto post by index (admin only)."""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ You don't have permission to use this command.")
        return
    
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text(
            "📝 **Usage:** /removepost <index>\n\n"
            "Use /listposts to see all posts with their indices."
        )
        return
    
    index = int(context.args[0]) - 1
    
    if 0 <= index < len(auto_posts):
        removed_post = auto_posts.pop(index)
        await update.message.reply_text(
            f"✅ **Post removed successfully!**\n\n"
            f"📝 **Removed:** {removed_post[:100]}{'...' if len(removed_post) > 100 else ''}"
        )
    else:
        await update.message.reply_text(f"❌ Invalid index. Use /listposts to see available posts.")

# Language group menu function removed - now using inline buttons

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command by showing the main menu."""
    try:
        logging.info("Processing /start command - building welcome message")
        welcome_text = (
            "🚀 **Welcome to TrustCoin (TBN)!** 🚀\n\n"
            "💎 **Revolutionary Mobile Mining on BSC**\n\n"
            "🎁 **Welcome Bonus:** 1,000 points\n"
            "⛏️ **Mining:** Up to 1,000 points/24h\n"
            "💰 **Conversion:** 1,000 points = 1 TBN\n\n"
            "📱 **Download:** https://www.trust-coin.site"
        )
        
        logging.info("Sending welcome message with menu")
        await update.message.reply_text(
            welcome_text, 
            reply_markup=build_main_menu(), 
            parse_mode="Markdown"
        )
        logging.info("Welcome message sent successfully")
    except Exception as e:
        logging.error(f"Error in start function: {e}")
        # Send simple message if there's an error
        try:
            await update.message.reply_text("Welcome to TrustCoin Bot! ✅")
        except Exception as e2:
            logging.error(f"Failed to send fallback message: {e2}")
        raise

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all callback queries from inline keyboards."""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "overview":
        text = (
            "📋 **Overview & Getting Started**\n\n"
            "🌟 TrustCoin (TBN) is a revolutionary blockchain-based rewards ecosystem on Binance Smart Chain <mcreference link=\"https://www.trust-coin.site/\" index=\"0\">0</mcreference>.\n\n"
            "🚀 **How to Get Started:**\n"
            "1️⃣ **Download the TrustCoin app** for iOS or Android and create your account\n"
            "🎁 Receive a **1,000-point welcome bonus** instantly!\n\n"
            "2️⃣ **Start 24-hour mining sessions** that continue even when the app is closed\n"
            "💾 Progress saves automatically every hour\n\n"
            "3️⃣ **Complete missions & spin the Lucky Wheel** for extra points\n"
            "🎯 Multiple ways to earn rewards daily\n\n"
            "4️⃣ **Convert your points to real TBN tokens** via automated smart contract\n"
            "💰 **1,000 points = 1 TBN token**\n\n"
            "📱 The mobile app is cross-platform (React Native) with chat and team features\n"
            "🔒 TrustCoin emphasizes transparency, community-driven development, and long-term value"
        )
        # Check if message has photo, if so send new message instead of editing
        if query.message.photo:
            await query.message.reply_text(text=text, reply_markup=build_main_menu(), parse_mode="Markdown")
        else:
            await query.edit_message_text(text=text, reply_markup=build_main_menu(), parse_mode="Markdown")

    elif data == "points":
        text = (
            "⛏️ **Mining & Points System**\n\n"
            "🕐 **24-Hour Mining Sessions:**\n"
            "• Earn up to **1,000 points per cycle**\n"
            "• Progress saves every hour automatically\n"
            "• Sessions resume after app restart\n\n"
            "📊 **Reward Formula:**\n"
            "`(session duration ÷ 86,400) × 1,000 points`\n\n"
            "📺 **Advertisement Rewards:**\n"
            "• Watch ads to unlock bonus strikes\n"
            "• Get multipliers for extra rewards\n\n"
            "💎 **Point-to-TBN Conversion:**\n"
            "• **Rate:** 1 TBN per 1,000 points\n"
            "• **Minimum:** 1,000 points redemption\n"
            "• **Daily Limit:** 100,000 points maximum\n"
            "• **Example:** 10,000 points = 10 TBN tokens\n\n"
            "🔗 **Smart Contract Features:**\n"
            "• Automated conversion on BSC\n"
            "• Gas fees initially covered by project\n"
            "• **Burn Rates:** 1% transfers, 0.5% conversions, 2% premium features"
        )
        # Check if message has photo, if so send new message instead of editing
        if query.message.photo:
            await query.message.reply_text(text=text, reply_markup=build_main_menu(), parse_mode="Markdown")
        else:
            await query.edit_message_text(text=text, reply_markup=build_main_menu(), parse_mode="Markdown")

    elif data == "missions":
        text = (
            "🎯 **Missions & Rewards System**\n\n"
            "🏆 **Trophy Missions (1-500 points):**\n"
            "• First mining session completion\n"
            "• Consecutive collection days\n"
            "• Referring new users\n"
            "• Daily login streaks\n\n"
            "💎 **Gem Missions (1,000-5,000 points):**\n"
            "• 30-day mining streaks\n"
            "• Top efficiency achievements\n"
            "• Completing all trophy missions\n\n"
            "🎁 **Chest Missions (2,000-10,000 points):**\n"
            "• 90-day consecutive streaks\n"
            "• Building a team of 20+ referrals\n"
            "• Collecting 100,000+ total points\n\n"
            "🪙 **Coin Missions (100-1,000 points):**\n"
            "• Daily tasks like sharing the app\n"
            "• Updating your profile\n"
            "• Joining community events\n\n"
            "🎰 **Lucky Wheel System:**\n"
            "• Spin for **1-1,500 points**\n"
            "• **3 strikes per cycle**\n"
            "• **6-hour cooldown** between cycles\n"
            "• **Probabilities:** 50% (1-100), 30% (101-200), 15% (201-300), 5% (301-500)\n"
            "• Watch ads for additional spins and multipliers!"
        )
        # Check if message has photo, if so send new message instead of editing
        if query.message.photo:
            await query.message.reply_text(text=text, reply_markup=build_main_menu(), parse_mode="Markdown")
        else:
            await query.edit_message_text(text=text, reply_markup=build_main_menu(), parse_mode="Markdown")

    elif data == "referral":
        text = (
            "👥 **Referral Program & Community**\n\n"
            "🔗 **Two-Tier Referral System:**\n"
            "• **Public codes** for everyone\n"
            "• **Exclusive codes** for top referrers\n\n"
            "🎁 **New User Benefits:**\n"
            "• **1,000-point welcome bonus** upon registration\n"
            "• **500 extra points** when using invitation code\n"
            "• Instant access to all features\n\n"
            "💰 **Referrer Rewards:**\n"
            "• **1,000 points per successful referral**\n"
            "• Share of referee's mining rewards\n"
            "• Recognition badges and bonuses\n"
            "• Leaderboard rankings\n\n"
            "👨‍👩‍👧‍👦 **Community Features:**\n"
            "• Team up with other miners\n"
            "• Chat in group conversations\n"
            "• Share mining strategies\n"
            "• Compete on global leaderboards\n"
            "• Participate in community events"
        )
        # Check if message has photo, if so send new message instead of editing
        if query.message.photo:
            await query.message.reply_text(text=text, reply_markup=build_main_menu(), parse_mode="Markdown")
        else:
            await query.edit_message_text(text=text, reply_markup=build_main_menu(), parse_mode="Markdown")

    elif data == "roadmap":
        text = (
            "📈 **Tokenomics & Roadmap**\n\n"
            "💰 **Supply Distribution (20B TBN Total):**\n"
            "• 🏆 **12B** - Mining Rewards Pool (60%)\n"
            "• 💧 **3B** - Liquidity Reserve (15%)\n"
            "• 🛠️ **3B** - Development Fund (15%)\n"
            "• 👥 **2B** - Team Allocation (10%)\n\n"
            "🔥 **Deflationary Mechanics:**\n"
            "• **1%** burn on all token transfers\n"
            "• **0.5%** burn on point conversions\n"
            "• **2%** burn on premium features\n"
            "• **Variable burns** for milestone achievements\n\n"
            "🏛️ **Governance & Staking:**\n"
            "• Stake TBN tokens for additional rewards\n"
            "• Token-weighted voting system\n"
            "• Variable APY based on staking duration\n"
            "• Premium app features unlock\n\n"
            "🗺️ **Development Roadmap:**\n"
            "**2025:** Foundation & Enhancement\n"
            "✅ Mining, missions, lucky wheel systems\n"
            "✅ Referral and advertisement integration\n\n"
            "**2025-2026:** Testing & Launch\n"
            "🔄 Security audits and optimization\n"
            "🚀 Mainnet launch on BSC\n"
            "🆔 KYC/AI verification systems\n\n"
            "**2026-2027:** Expansion & Innovation\n"
            "📈 Major exchange listings\n"
            "🏦 DeFi protocol integration\n"
            "🌐 Trust blockchain development\n"
            "🏛️ DAO governance implementation\n"
            "🎨 NFT marketplace launch\n"
            "🌍 Metaverse partnerships\n"
            "🌉 Cross-chain bridge development\n"
            "💳 Global payment system integration"
        )
        # Check if message has photo, if so send new message instead of editing
        if query.message.photo:
            await query.message.reply_text(text=text, reply_markup=build_main_menu(), parse_mode="Markdown")
        else:
            await query.edit_message_text(text=text, reply_markup=build_main_menu(), parse_mode="Markdown")

    elif data == "download":
        # Download app section with direct links
        download_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📱 Download for iOS", url="https://apps.apple.com/app/trustcoin")],
            [InlineKeyboardButton("🤖 Download for Android", url="https://play.google.com/store/apps/details?id=com.jawad06_dev.trustcoinmobile.v3")],
            [InlineKeyboardButton("🌐 Visit Official Website", url="https://www.trust-coin.site")],
            [InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="back")],
        ])
        text = (
            "📱 **Download TrustCoin App**\n\n"
            "🚀 **Get started with TrustCoin today!**\n\n"
            "📲 **Available on both platforms:**\n"
            "• iOS App Store\n"
            "• Google Play Store\n\n"
            "🎁 **What you get:**\n"
            "• **1,000 points welcome bonus**\n"
            "• **24/7 mining capability**\n"
            "• **Cross-platform compatibility**\n"
            "• **Real-time chat & team features**\n"
            "• **Secure blockchain integration**\n\n"
            "💡 **System Requirements:**\n"
            "• iOS 12.0+ or Android 6.0+\n"
            "• Internet connection\n"
            "• 50MB storage space\n\n"
            "🔗 Click the buttons below to download:"
        )
        await query.edit_message_text(
            text, reply_markup=download_keyboard, parse_mode="Markdown"
        )

    elif data == "security":
        text = (
            "🔒 **Security & Anti-Cheat System**\n\n"
            "🛡️ **Multi-Layer Security:**\n"
            "• **Device fingerprinting** to prevent multi-account abuse\n"
            "• **Real-time session validation** with time-based authentication\n"
            "• **AI-powered pattern analysis** to detect automation and cheating\n"
            "• **Geographic consistency checks** for authentic user behavior\n\n"
            "⚖️ **Fair Play Enforcement:**\n"
            "• **One account per person** policy\n"
            "• **Real device requirement** - no emulators\n"
            "• **No automation tools** allowed\n"
            "• **Permanent bans** for violations\n\n"
            "🔐 **Blockchain Security:**\n"
            "• **Smart contract audits** by leading security firms\n"
            "• **Deflationary mechanics** for real value\n"
            "• **Anti-whale protection** mechanisms\n"
            "• **Transparent on-chain operations**\n\n"
            "🚨 **Fraud Prevention:**\n"
            "• **Advanced encryption** for all data\n"
            "• **Behavioral analysis** algorithms\n"
            "• **Community reporting** system\n"
            "• **24/7 monitoring** infrastructure\n\n"
            "✅ **Your safety is our priority!**"
        )
        # Check if message has photo, if so send new message instead of editing
        if query.message.photo:
            await query.message.reply_text(text=text, reply_markup=build_main_menu(), parse_mode="Markdown")
        else:
            await query.edit_message_text(text=text, reply_markup=build_main_menu(), parse_mode="Markdown")

    elif data == "faq":
        text = (
            "❓ **Frequently Asked Questions**\n\n"
            "**Q1: How do I start mining?**\n"
            "A: Download the app, register, and tap the mining button. Sessions run for 24 hours automatically.\n\n"
            "**Q2: When can I withdraw my TBN tokens?**\n"
            "A: Token conversion will be available after mainnet launch on BSC (2025-2026).\n\n"
            "**Q3: Is TrustCoin free to use?**\n"
            "A: Yes! The app is completely free. You only need internet connection.\n\n"
            "**Q4: How many accounts can I have?**\n"
            "A: Only ONE account per person. Multiple accounts will result in permanent ban.\n\n"
            "**Q5: What's the minimum withdrawal?**\n"
            "A: Minimum conversion is 1,000 points = 1 TBN token.\n\n"
            "**Q6: Can I use emulators or bots?**\n"
            "A: No! Only real devices are allowed. Automation tools are strictly prohibited.\n\n"
            "**Q7: How do referrals work?**\n"
            "A: Share your referral code. You get 1,000 points per successful referral.\n\n"
            "**Q8: Is my data safe?**\n"
            "A: Yes! We use advanced encryption and security measures to protect your data.\n\n"
            "**Q9: When will TBN be listed on exchanges?**\n"
            "A: Major exchange listings are planned for 2026-2027 after mainnet launch.\n\n"
            "**Q10: How can I contact support?**\n"
            "A: Join our Telegram group or visit our website for support."
        )
        # Check if message has photo, if so send new message instead of editing
        if query.message.photo:
            await query.message.reply_text(text=text, reply_markup=build_main_menu(), parse_mode="Markdown")
        else:
            await query.edit_message_text(text=text, reply_markup=build_main_menu(), parse_mode="Markdown")

    elif data == "social":
        # Social links as buttons
        social_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🌐 Website", url="https://www.trust-coin.site")],
            [InlineKeyboardButton("📘 Facebook ➡️", url="https://www.facebook.com/people/TrustCoin/61579302546502/")],
            [InlineKeyboardButton("✈️ Telegram Group ➡️", url="https://t.me/+7A9zYR8BCU03ODA0")],
            [InlineKeyboardButton("🐦 X/Twitter ➡️", url="https://x.com/TBNTrustCoin")],
            [InlineKeyboardButton("Back to Main Menu", callback_data="back")],
        ])
        await query.edit_message_text(
            "Choose a link to open:", reply_markup=social_keyboard
        )

    elif data == "language_groups":
        # Language groups as direct buttons with flags - Only English now
        language_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🇺🇸 English Group", url="https://t.me/tructcoin_bot")],
            [InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="back")],
        ])
        await query.edit_message_text(
            "Join our TrustCoin community:",
            reply_markup=language_keyboard
        )

    # Language group handlers removed - now using direct URL buttons

    elif data == "back":
        # Check if message has photo, if so send new message instead of editing
        if query.message.photo:
            await query.message.reply_text(
                "Main menu:", reply_markup=build_main_menu()
            )
        else:
            await query.edit_message_text(
                "Main menu:", reply_markup=build_main_menu()
            )

    else:
        # Check if message has photo, if so send new message instead of editing
        if query.message.photo:
            await query.message.reply_text(
                "Invalid option. Returning to main menu.", reply_markup=build_main_menu()
            )
        else:
            await query.edit_message_text(
                "Invalid option. Returning to main menu.", reply_markup=build_main_menu()
            )

# Flask app for webhook
flask_app = Flask(__name__)

@flask_app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming webhook updates."""
    try:
        update = Update.de_json(request.get_json(force=True), bot_app)
        asyncio.run(bot_app.process_update(update))
        return 'OK'
    except Exception as e:
        logging.error(f"Error processing webhook: {e}")
        return 'Error', 500

@flask_app.route('/health')
def health():
    """Health check endpoint."""
    return 'OK'

@flask_app.route('/')
def home():
    """Home endpoint."""
    return 'TrustCoin Bot is running!'

def run_flask():
    """Run Flask app in a separate thread."""
    port = int(os.getenv('PORT', 8443))
    
    # Suppress Flask development server warning
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    
    # Always run Flask server for render.com compatibility
    flask_app.run(host='0.0.0.0', port=port, debug=False)

def main() -> None:
    """Initialize the bot."""
    global bot_app
    
    try:
        # Create health check file for Docker
        with open('/tmp/bot_healthy', 'w') as f:
            f.write('starting')
            
        bot_app = ApplicationBuilder().token(BOT_TOKEN_ENG).build()
        
        # Track /start command usage
        async def track_start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
            try:
                logging.info(f"Received /start command from user {update.effective_user.id if update.effective_user else 'Unknown'}")
                if update.effective_user:
                    track_user_activity(update.effective_user.id, update.effective_user.username, "start_command")
                await start(update, context)
                logging.info("Successfully processed /start command")
            except Exception as e:
                logging.error(f"Error in /start command: {e}")
                raise
        
        # Add command handlers
        bot_app.add_handler(CommandHandler("start", track_start_command))
        bot_app.add_handler(CommandHandler("stats", admin_stats))
        bot_app.add_handler(CommandHandler("addpost", admin_add_post))
        bot_app.add_handler(CommandHandler("listposts", admin_list_posts))
        bot_app.add_handler(CommandHandler("removepost", admin_remove_post))
        
        # Add callback query handler
        bot_app.add_handler(CallbackQueryHandler(button_handler))
        
        # Add chat member handler for welcome messages
        bot_app.add_handler(ChatMemberHandler(handle_chat_member_update, ChatMemberHandler.CHAT_MEMBER))
        
        # Add handler for all messages to debug FIRST
        async def debug_all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
            if update.message:
                chat_type = update.effective_chat.type
                chat_id = update.effective_chat.id
                user_id = update.effective_user.id if update.effective_user else "Unknown"
                text = update.message.text[:50] if update.message.text else 'No text'
                message_type = "text" if update.message.text else "other"
                logging.info(f"🔍 DEBUG - Message: Chat ID: {chat_id}, Type: {chat_type}, User: {user_id}, Text: {text}, MsgType: {message_type}")
        
        bot_app.add_handler(MessageHandler(filters.ALL, debug_all_messages), group=0)
        
        # Add message handler for group interactions
        bot_app.add_handler(MessageHandler(
            filters.TEXT & (filters.ChatType.GROUP | filters.ChatType.SUPERGROUP), 
            handle_group_message
        ), group=1)
        
        # Force polling mode - ignore webhook URL
        webhook_url = None  # Force polling mode
        
        # Flask server is handled by app.py on Render
        # Don't start Flask server here to avoid port conflicts
        logging.info("Bot starting without Flask server (handled by app.py)")
        
        # Enable auto-posting
        logging.info("✅ Auto-posting enabled - will post every 2 minutes")
        
        # Start auto-posting in background
        async def start_auto_posting():
            await asyncio.sleep(60)  # Wait 1 minute before first post
            while True:
                try:
                    await auto_post_to_groups()
                    await asyncio.sleep(AUTO_POST_INTERVAL)  # Wait between posts
                except Exception as e:
                    logging.error(f"Error in auto-posting loop: {e}")
                    await asyncio.sleep(60)  # Wait 1 minute on error
        
        # Start auto-posting task
        asyncio.create_task(start_auto_posting())
        
        if webhook_url:
            # Production mode with webhook
            logging.info("Starting English bot in webhook mode...")
            
            # Set webhook
            asyncio.run(bot_app.bot.set_webhook(url=webhook_url))
            
            with open('/tmp/bot_healthy', 'w') as f:
                f.write('running')
            
            logging.info("🤖 TrustCoin Bot is now active with enhanced group features!")
            logging.info("✅ Welcome messages enabled")
            logging.info("✅ User monitoring enabled")
            logging.info("✅ Group interaction enabled")
            
            # Keep the main thread alive
            import time
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                logging.info("Bot stopped gracefully")
        else:
            # Development mode with polling
            logging.info("Starting English bot in polling mode...")
            
            # Auto-posting disabled for testing
            # def start_scheduler():
            #     loop = asyncio.new_event_loop()
            #     asyncio.set_event_loop(loop)
            #     loop.create_task(auto_post_scheduler())
            #     loop.run_forever()
            # 
            # scheduler_thread = threading.Thread(target=start_scheduler, daemon=True)
            # scheduler_thread.start()
            
            # Update health status
            try:
                with open('/tmp/bot_healthy', 'w') as f:
                    f.write('running')
            except:
                pass
            
            logging.info("🤖 TrustCoin Bot FULL VERSION is now active with enhanced group features!")
            logging.info("✅ Welcome messages enabled")
            logging.info("✅ Auto-posting disabled for testing")
            logging.info("✅ User monitoring enabled")
            logging.info("✅ Group interaction enabled")
            logging.info("✅ All advanced features available")
            
            # Start Flask server in background thread
            from flask import Flask
            import threading
            
            flask_app = Flask(__name__)
            
            @flask_app.route('/')
            def home():
                return "TrustCoin Bot FULL VERSION is running! ✅"
            
            @flask_app.route('/health')
            def health():
                return {"status": "healthy", "bot": "running", "version": "full"}
            
            @flask_app.route('/webhook', methods=['POST'])
            def webhook():
                return "Webhook not configured for polling mode", 404
            
            # Start Flask in background thread
            def start_flask():
                port = int(os.environ.get('PORT', 8000))
                logging.info(f"Starting Flask server on port {port}")
                flask_app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
            
            flask_thread = threading.Thread(target=start_flask, daemon=True)
            flask_thread.start()
            
            # Give Flask time to start
            import time
            time.sleep(3)
            
            # Run bot polling in main thread (no event loop issues)
            logging.info("Starting bot polling in main thread...")
            bot_app.run_polling(drop_pending_updates=True)
            
    except InvalidToken:
        logging.error("❌ Invalid bot token. Please check your BOT_TOKEN_ENG.")
        # Remove health file on error
        try:
            os.remove('/tmp/bot_healthy')
        except:
            pass
        raise
    except Exception as e:
        logging.error(f"❌ Error starting English bot: {e}")
        # Remove health file on error
        try:
            os.remove('/tmp/bot_healthy')
        except:
            pass
        raise

if __name__ == "__main__":
    main()
