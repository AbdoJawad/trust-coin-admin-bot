#!/usr/bin/env python3
"""
Flask app that runs TrustCoin bot in background
"""
import os
import threading
import time
from flask import Flask

app = Flask(__name__)

# Global variable to track bot status
bot_running = False

@app.route('/')
def home():
    return f"TrustCoin Bot is running! Status: {'Active' if bot_running else 'Starting...'}"

@app.route('/health')
def health():
    return {"status": "healthy", "bot_running": bot_running}

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle Telegram webhook - not used in polling mode"""
    return "Webhook not configured for polling mode", 404

def run_bot():
    """Run the bot in background"""
    global bot_running
    try:
        print("Starting bot in background...")
        import bot
        bot_running = True
        bot.main()
    except Exception as e:
        print(f"Bot error: {e}")
        bot_running = False

if __name__ == "__main__":
    # Start bot in background thread
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Give bot time to start
    time.sleep(1)
    
    # Start Flask server
    port = int(os.environ.get('PORT', 8000))
    print(f"Starting Flask on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
