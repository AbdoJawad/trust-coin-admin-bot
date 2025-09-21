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
    return "OK"

def run_bot():
    """Run the Telegram bot in a separate thread"""
    try:
        print("Starting Telegram bot...")
        bot_status["running"] = True
        
        # Import and modify the bot to not start Flask
        import bot
        
        # Disable Flask in the bot
        bot.run_flask = lambda: None
        
        # Run the bot
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
