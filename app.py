#!/usr/bin/env python3
"""
Main entry point for TrustCoin Bot on Render.com
"""
import os
import sys
import threading
import time
from flask import Flask, jsonify

# Add the ENGLISH directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ENGLISH'))

# Create Flask app for Render.com compatibility
app = Flask(__name__)

# Global variable to track bot status
bot_status = {"running": False, "error": None}

@app.route('/')
def home():
    return f"TrustCoin Bot is running! Status: {bot_status}"

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "bot": "TrustCoin", "bot_running": bot_status["running"]})

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle Telegram webhook updates"""
    try:
        import json
        from flask import request
        
        # Get the update from Telegram
        update_data = request.get_json()
        
        if update_data:
            # Import the bot's webhook handler
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ENGLISH'))
            
            from bot import bot_app
            import asyncio
            from telegram import Update
            
            # Process the update
            if bot_app:
                update = Update.de_json(update_data, bot_app.bot)
                # Run the update processing
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(bot_app.process_update(update))
                loop.close()
        
        return "OK"
    except Exception as e:
        print(f"Webhook error: {e}")
        return "Error", 500

def run_bot():
    """Run the Telegram bot in a separate thread"""
    try:
        print("Starting Telegram bot...")
        bot_status["running"] = True
        
        # Import bot module
        import bot
        import os
        
        # Force polling mode by removing WEBHOOK_URL
        os.environ.pop('WEBHOOK_URL', None)
        
        # Disable Flask in the bot
        bot.run_flask = lambda: None
        
        # Run the bot in polling mode
        bot.main()
        
    except Exception as e:
        print(f"Bot error: {e}")
        bot_status["error"] = str(e)
        bot_status["running"] = False

# Start the bot immediately when the module is imported
print("Starting Telegram bot in background...")
bot_thread = threading.Thread(target=run_bot, daemon=True)
bot_thread.start()

if __name__ == "__main__":
    # Get port from environment
    port = int(os.environ.get('PORT', 8443))
    print(f"Starting Flask app on port {port}")
    
    # Start Flask app (this blocks)
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
