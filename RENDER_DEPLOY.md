# 🚀 Deploying TrustCoin Bot to Render.com

## Quick Deploy Guide

### 1. **Connect GitHub Repository**
- Go to [Render.com](https://render.com)
- Click "New +" → "Web Service"
- Connect your GitHub repository: `AbdoJawad/TrustCoin-Bot`

### 2. **Service Configuration**
```
Name: trustcoin-english-bot
Environment: Python 3
Build Command: pip install -r requirements.txt
Start Command: python ENGLISH/bot.py
```

### 3. **Environment Variables**
Add these environment variables in Render dashboard:

| Variable | Value | Description |
|----------|-------|-------------|
| `BOT_TOKEN_ENG` | `7512597854:AAH...` | English Bot Token |
| `BOT_TOKEN_ARA` | `8290216301:AAE...` | Arabic Bot Token |
| `BOT_TOKEN_FR` | `8375639193:AAG...` | French Bot Token |
| `PORT` | `8443` | Port for Flask server |
| `DEBUG` | `False` | Production mode |
| `APP_ENV` | `production` | Environment type |

### 4. **Multiple Bot Deployment**

#### Option A: Single Service (Recommended)
Deploy one bot per service:
- **English Bot**: Use `python ENGLISH/bot.py`
- **Arabic Bot**: Use `python ARABIC/bot.py`  
- **French Bot**: Use `python FRANCE/bot.py`

#### Option B: Background Workers
If you don't need web interface:
- Service Type: "Background Worker"
- No PORT binding required

### 5. **Advanced Configuration**

#### Dockerfile Deployment (Alternative)
```dockerfile
# Use our existing Dockerfile
# Render will automatically detect it
```

#### Health Check Endpoint
Your bot will be accessible at:
- `https://your-service-url.onrender.com/health`
- `https://your-service-url.onrender.com/` (status page)

### 6. **Troubleshooting**

#### Port Binding Issues
✅ **Fixed**: All bots now run Flask server automatically
- Flask runs on separate thread
- Responds to health checks
- Compatible with Render's port requirements

#### Environment Variables
- Never commit `.env` file to Git
- Use Render's Environment Variables section
- Test locally first with `.env` file

#### Multiple Instances
To run all bots simultaneously:
1. Create 3 separate Render services
2. Use different bot tokens for each
3. Each will run on its own subdomain

### 7. **Cost Optimization**

#### Free Tier Usage
- Free tier allows 750 hours/month
- Multiple services share the limit
- Consider Background Workers for better resource usage

#### Scaling Options
- **Starter**: $7/month per service
- **Standard**: $25/month per service
- Background Workers are cheaper

## 📞 Support

If deployment fails:
1. Check Render logs for errors
2. Verify all environment variables are set
3. Ensure bot tokens are valid
4. Check GitHub repository permissions

---
**Last Updated**: December 2024
**Compatible with**: Render.com Free & Paid tiers
