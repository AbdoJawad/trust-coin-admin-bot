# 🚀 TrustCoin Bot - Enhanced Group Management

A powerful Telegram bot for TrustCoin community with advanced group management features.

## ✨ Features

### 🎯 Core Features
- **Welcome Messages**: Automatically welcomes new group members
- **Auto-Posting**: Posts promotional content every 2 minutes (configurable)
- **User Monitoring**: Tracks user activity and engagement
- **Interactive Responses**: Responds to keywords and mentions
- **Admin Commands**: Manage posts and view statistics

### 🛡️ Security Features
- Admin-only commands with user ID verification
- Anti-spam protection
- Secure token management
- Activity logging

### 📊 Analytics
- User activity tracking
- Message statistics
- Group engagement metrics
- Real-time monitoring

## 🔧 Setup Instructions

### 1. Prerequisites
- Python 3.8+
- Telegram Bot Token from @BotFather
- Group Admin permissions

### 2. Installation

```bash
# Clone the repository
git clone https://github.com/AbdoJawad/TrustCoin-Bot.git
cd TrustCoin-Bot

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
```

### 3. Configuration

Edit `.env` file with your settings:

```env
# Bot Token from @BotFather
BOT_TOKEN_ENG=your_bot_token_here

# Admin User IDs (comma-separated)
ADMIN_USER_IDS=your_user_id_here

# Group Chat IDs for auto-posting (comma-separated)
GROUP_CHAT_IDS=your_group_chat_id_here

# Auto-posting interval in seconds (default: 120 = 2 minutes)
AUTO_POST_INTERVAL=120
```

### 4. Getting Required IDs

#### Get Your User ID:
1. Message @userinfobot on Telegram
2. Copy your User ID

#### Get Group Chat ID:
1. Add bot to your group
2. Send a message in the group
3. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
4. Find the negative chat ID in the response

### 5. Run the Bot

```bash
# Local development
python ENGLISH/bot.py

# Or use the provided script
python run_english_bot.bat  # Windows
```

## 🎮 Usage

### Admin Commands
- `/stats` - View bot statistics
- `/addpost <message>` - Add new auto-post
- `/listposts` - List all auto-posts
- `/removepost <index>` - Remove auto-post by index

### Group Features
- **Automatic welcome** for new members
- **Keyword responses** (mining, points, app, referral, token, help)
- **Mention handling** with helpful responses
- **Auto-posting** every 2 minutes

## 🚀 Deployment

### Option 1: Render.com (Recommended)
1. Fork this repository
2. Create account on [Render.com](https://render.com)
3. Create new Web Service
4. Connect your GitHub repository
5. Set environment variables in Render dashboard

### Option 2: Heroku
1. Install Heroku CLI
2. Create new Heroku app
3. Set environment variables
4. Deploy using Git

### Option 3: VPS/Server
1. Clone repository on server
2. Install dependencies
3. Set up systemd service
4. Configure reverse proxy (nginx)

## 📁 Project Structure

```
TrustCoin-Bot/
├── ENGLISH/
│   └── bot.py              # Main bot file
├── requirements.txt        # Python dependencies
├── .env.example           # Environment template
├── .gitignore            # Git ignore rules
└── README.md             # This file
```

## 🔒 Security Notes

- **Never commit** `.env` files to Git
- **Keep bot tokens** secure and private
- **Use environment variables** for sensitive data
- **Regularly update** dependencies
- **Monitor bot activity** for suspicious behavior

## 🛠️ Customization

### Adding New Auto-Posts
```python
# Use admin command
/addpost 🚀 New TrustCoin update! Check out our latest features!

# Or edit DEFAULT_AUTO_POSTS in bot.py
```

### Changing Response Probability
```python
# In bot.py, modify this line:
if keyword in message_text.lower() and random.random() < 0.3:  # 30% chance
```

### Adding New Keywords
```python
# In keywords_responses dictionary:
keywords_responses = {
    "your_keyword": "Your response message",
    # ... existing keywords
}
```

## 📊 Monitoring

### Logs
The bot logs all important activities:
- New member welcomes
- Auto-post deliveries
- User interactions
- Error messages

### Statistics
Use `/stats` command to monitor:
- User engagement
- Message volume
- Bot performance

## 🐛 Troubleshooting

### Bot Not Responding
1. Check bot permissions in group
2. Verify environment variables
3. Check logs for errors

### Auto-Posts Not Working
1. Verify `GROUP_CHAT_IDS` in `.env`
2. Check bot send message permissions
3. Review error logs

### Welcome Messages Not Sent
1. Ensure bot has "Add new members" permission
2. Check if bot can send messages
3. Verify bot is not restricted

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make your changes
4. Test thoroughly
5. Submit pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

- **Telegram**: [TrustCoin Group](https://t.me/+djORe9HGRi45ZDdk)
- **Website**: [trust-coin.site](https://www.trust-coin.site)
- **Issues**: [GitHub Issues](https://github.com/AbdoJawad/TrustCoin-Bot/issues)

## 🙏 Acknowledgments

- Telegram Bot API
- python-telegram-bot library
- TrustCoin community

---

**Made with ❤️ for the TrustCoin community**
