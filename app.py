#!/usr/bin/env python3
"""
Redirect to full bot - app.py is disabled
"""
print("app.py is disabled - redirecting to full bot...")
import sys
import os

# Add ENGLISH directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ENGLISH'))

# Change to ENGLISH directory and run the full bot
os.chdir(os.path.join(os.path.dirname(__file__), 'ENGLISH'))
import bot
bot.main()
