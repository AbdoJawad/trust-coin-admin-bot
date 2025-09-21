#!/usr/bin/env python3
"""
Main entry point for TrustCoin Bot on Render.com
"""
import os
import sys

# Add the ENGLISH directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ENGLISH'))

# Import and run the bot
if __name__ == "__main__":
    from bot import main
    main()
