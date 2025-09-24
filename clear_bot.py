#!/usr/bin/env python3
"""
Script to completely clear bot conflicts and reset webhook
"""
import asyncio
import os
from telegram import Bot
from dotenv import load_dotenv

load_dotenv()

async def clear_bot_completely():
    """Clear all bot conflicts and reset webhook"""
    bot_token = os.getenv('BOT_TOKEN_ENG')
    if not bot_token:
        print("❌ BOT_TOKEN_ENG not found")
        return
    
    bot = Bot(token=bot_token)
    
    try:
        print("🔄 Getting bot info...")
        me = await bot.get_me()
        print(f"✅ Bot: @{me.username}")
        
        print("🔄 Deleting webhook...")
        await bot.delete_webhook(drop_pending_updates=True)
        print("✅ Webhook deleted")
        
        print("🔄 Getting webhook info...")
        webhook_info = await bot.get_webhook_info()
        print(f"Webhook URL: {webhook_info.url}")
        print(f"Pending updates: {webhook_info.pending_update_count}")
        
        if webhook_info.url:
            print("🔄 Force deleting webhook again...")
            await bot.delete_webhook(drop_pending_updates=True)
            await asyncio.sleep(5)
        
        print("🔄 Clearing pending updates...")
        updates = await bot.get_updates(limit=100, timeout=1)
        print(f"Cleared {len(updates)} pending updates")
        
        print("✅ Bot cleared successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(clear_bot_completely())
