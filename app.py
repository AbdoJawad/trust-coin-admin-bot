#!/usr/bin/env python3
"""
Main entry point for TrustCoin Bot on Render.com
"""
import os
import sys
import threading
from flask import Flask

# Add the ENGLISH directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ENGLISH'))

# Create Flask app for Render.com compatibility
app = Flask(__name__)

@app.route('/')
def home():
    return "TrustCoin Bot is running!"

@app.route('/health')
def health():
    return {"status": "healthy", "bot": "TrustCoin"}

@app.route('/webhook', methods=['POST'])
def webhook():
    # This will be handled by the bot's webhook handler
    return "OK"

def run_bot():
    """Run the Telegram bot in a separate thread"""
    try:
        from bot import main
        main()
    except Exception as e:
        print(f"Bot error: {e}")

if __name__ == "__main__":
    # Start the bot in a background thread
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Start Flask app
    port = int(os.environ.get('PORT', 8443))
    app.run(host='0.0.0.0', port=port)
