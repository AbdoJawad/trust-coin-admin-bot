#!/usr/bin/env python3
"""
Kill Bots Script - يوقف جميع عمليات البوتات
هذا السكريبت يساعد في حل مشكلة تضارب البوتات
"""

import os
import sys
import signal
import psutil
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def print_header():
    """Print script header."""
    print("=" * 60)
    print("🤖 TrustCoin Bot Killer Script")
    print("=" * 60)
    print("هذا السكريبت سيقوم بإيقاف جميع عمليات البوتات المشغلة")
    print("=" * 60)

def kill_python_bots():
    """Kill all Python bot processes."""
    print("\n🔍 البحث عن عمليات Python...")
    killed_count = 0
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Check if process is a Python bot
            if proc.info['name'] and 'python' in proc.info['name'].lower():
                cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                if any(keyword in cmdline.lower() for keyword in ['bot.py', 'telegram', 'trustcoin']):
                    print(f"🔪 قتل العملية: PID {proc.info['pid']} - {cmdline[:50]}...")
                    proc.kill()
                    killed_count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    print(f"✅ تم إيقاف {killed_count} عملية Python")

def delete_webhooks():
    """Delete webhooks for all bots."""
    print("\n🔗 حذف Webhooks...")
    
    tokens = [
        os.getenv('BOT_TOKEN_ENG'),
        os.getenv('BOT_TOKEN_ARA'),
        os.getenv('BOT_TOKEN_FR')
    ]
    
    for i, token in enumerate(tokens, 1):
        if token:
            try:
                url = f"https://api.telegram.org/bot{token}/deleteWebhook"
                response = requests.post(url, timeout=10)
                if response.status_code == 200:
                    print(f"✅ تم حذف webhook للبوت {i}")
                else:
                    print(f"⚠️ فشل حذف webhook للبوت {i}")
            except Exception as e:
                print(f"❌ خطأ في حذف webhook للبوت {i}: {e}")
        else:
            print(f"⚠️ لم يتم العثور على token للبوت {i}")

def kill_docker_containers():
    """Kill Docker containers."""
    print("\n🐳 إيقاف حاويات Docker...")
    
    try:
        # Stop TrustCoin containers
        os.system("docker stop $(docker ps -q --filter name=trustcoin) 2>/dev/null")
        print("✅ تم إيقاف حاويات Docker")
    except Exception as e:
        print(f"⚠️ تعذر إيقاف حاويات Docker: {e}")

def check_running_bots():
    """Check if any bots are still running."""
    print("\n🔍 فحص البوتات المتبقية...")
    
    tokens = [
        os.getenv('BOT_TOKEN_ENG'),
        os.getenv('BOT_TOKEN_ARA'),
        os.getenv('BOT_TOKEN_FR')
    ]
    
    for i, token in enumerate(tokens, 1):
        if token:
            try:
                url = f"https://api.telegram.org/bot{token}/getMe"
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    print(f"🟢 البوت {i} متاح ولكن لا يعمل")
                else:
                    print(f"🔴 البوت {i} غير متاح")
            except Exception as e:
                print(f"🔴 البوت {i} غير متاح: {e}")

def main():
    """Main function."""
    print_header()
    
    try:
        # Kill Python processes
        kill_python_bots()
        
        # Delete webhooks
        delete_webhooks()
        
        # Kill Docker containers
        kill_docker_containers()
        
        # Wait a moment
        import time
        time.sleep(2)
        
        # Check status
        check_running_bots()
        
        print("\n" + "=" * 60)
        print("✅ تم إنهاء العملية بنجاح!")
        print("✅ يمكنك الآن تشغيل البوتات مرة أخرى")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\n⛔ تم إلغاء العملية بواسطة المستخدم")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ خطأ غير متوقع: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
