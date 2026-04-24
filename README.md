# MAKAUT ME Bot — Replit Setup Guide

## Step 1: Upload to Replit
1. Go to https://replit.com → Create Repl → **Import from ZIP**
2. Upload this ZIP file
3. Language: **Python**

## Step 2: Set BOT_TOKEN (Secrets)
1. In Replit sidebar → click 🔒 **Secrets** (padlock icon)
2. Add new secret:
   - **Key:** `BOT_TOKEN`
   - **Value:** Your Telegram bot token (from @BotFather)
3. Click **Add Secret**

## Step 3: (Optional) Set Storage Channel
If you use lecture video storage channel:
- **Key:** `STORAGE_CHANNEL_ID`
- **Value:** Your channel ID (e.g. `-1001234567890`)

## Step 4: Run the Bot
- Click the big green ▶ **Run** button
- You should see: `🤖 MAKAUT ME Bot started.`

## Step 5: Keep Bot Alive 24/7 (Important!)
Replit free plan sleeps after ~1 hour of inactivity.
Use **UptimeRobot** (free) to ping your Replit URL every 5 minutes:

1. Copy your Replit app URL: `https://YOUR-REPL-NAME.YOUR-USERNAME.repl.co`
2. Go to https://uptimerobot.com → Sign up free
3. Add New Monitor:
   - Monitor Type: **HTTP(s)**
   - URL: your Replit URL
   - Interval: **5 minutes**
4. Done — bot stays awake 24/7!

## Force Join Channels
The bot requires users to join these channels before use:
- https://t.me/mechanical_Gate_ese_je_notes2027
- https://t.me/mechanical_quiz_ese_gate_je

**Important:** Add your bot as **Admin** in both channels
(only "Add Members" permission needed).

## Troubleshooting
- **Bot not responding?** Check Secrets → BOT_TOKEN is set correctly
- **Force join not working?** Make sure bot is Admin in both channels
- **Videos not sending?** Set STORAGE_CHANNEL_ID secret correctly
