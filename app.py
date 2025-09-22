#!/usr/bin/env python3
"""
Simple TrustCoin Bot for Render.com
"""
import os
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get bot token
BOT_TOKEN = os.getenv('BOT_TOKEN_ENG')

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN_ENG not found!")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    keyboard = [
        [InlineKeyboardButton("📋 Overview", callback_data="overview")],
        [InlineKeyboardButton("⛏️ Mining", callback_data="mining")],
        [InlineKeyboardButton("🌐 Website", url="https://www.trust-coin.site")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        "🚀 **Welcome to TrustCoin (TBN)!** 🚀\n\n"
        "💎 **Revolutionary Mobile Mining on BSC**\n\n"
        "🎁 **Welcome Bonus:** 1,000 points\n"
        "⛏️ **Mining:** Up to 1,000 points/24h\n"
        "💰 **Conversion:** 1,000 points = 1 TBN\n\n"
        "📱 **Download:** https://www.trust-coin.site"
    )
    
    await update.message.reply_text(
        welcome_text, 
        reply_markup=reply_markup, 
        parse_mode="Markdown"
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button clicks"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "overview":
        text = (
            "📋 **TrustCoin Overview**\n\n"
            "🌟 Revolutionary blockchain rewards ecosystem\n"
            "🔗 Built on Binance Smart Chain\n"
            "💎 Deflationary tokenomics\n"
            "🎯 Fair distribution model\n\n"
            "Join the future of mobile mining!"
        )
    elif query.data == "mining":
        text = (
            "⛏️ **Mining System**\n\n"
            "🔥 **24-hour mining cycles**\n"
            "📊 **Up to 1,000 points per session**\n"
            "⚡ **No energy consumption**\n"
            "📱 **Mobile-first design**\n\n"
            "Start mining now in the app!"
        )
    else:
        text = "Invalid option!"
    
    await query.edit_message_text(text, parse_mode="Markdown")

def main():
    """Main function"""
    print("Starting TrustCoin Bot...")
    
    # Create application
    bot_app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Add handlers
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CallbackQueryHandler(button_handler))
    
    # Start bot in background
    import threading
    import asyncio
    
    def run_bot():
        print("Bot is running...")
        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            # Use asyncio.run instead of run_polling for better thread support
            async def start_bot():
                async with bot_app:
                    await bot_app.start()
                    await bot_app.updater.start_polling(drop_pending_updates=True)
                    # Keep running
                    await asyncio.Event().wait()
            
            loop.run_until_complete(start_bot())
        except Exception as e:
            print(f"Bot error: {e}")
        finally:
            loop.close()
    
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Give bot time to start
    import time
    time.sleep(2)
    
    # Start simple Flask server for Render
    from flask import Flask
    app = Flask(__name__)
    
    @app.route('/')
    def home():
        return "TrustCoin Bot is running! ✅"
    
    @app.route('/health')
    def health():
        return {
            "status": "healthy", 
            "bot": "running",
            "bot_thread_alive": bot_thread.is_alive(),
            "token_loaded": bool(BOT_TOKEN)
        }
    
    port = int(os.environ.get('PORT', 8000))
    print(f"Starting Flask on port {port}")
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    main()
