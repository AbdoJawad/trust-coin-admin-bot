#!/usr/bin/env python3
"""
Redirect to full bot - app.py is disabled
"""
print("app.py is disabled - redirecting to full bot...")
import sys
import os

# Change to ENGLISH directory and run the full bot
os.chdir('ENGLISH')
import bot
bot.main()
