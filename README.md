# RamadanHabitTracker
 Ramadan Habit Tracker
A multi-platform bot that helps Muslims track their daily worship activities during Ramadan.

Features
Track Multiple Habits:

Five daily prayers
Taraweeh prayers
Tahajjud prayers
Quran recitation (pages)
Quran translation reading (pages)
Fasting
Progress Tracking:

Daily progress summaries
Historical logs
Performance statistics
Multi-Platform Support:

Telegram bot interface
WhatsApp integration
Daily reminders at 8 PM
Social Features:

Leaderboard for friendly competition
Export your data as CSV
Setup Instructions
Prerequisites
Python 3.7+
Telegram Bot Token (from BotFather)
WhatsApp Business API credentials (optional)
Environment Variables
Set the following environment variables:

BOT_TOKEN: Your Telegram bot token
WHATSAPP_TOKEN: WhatsApp API token (optional)
WHATSAPP_PHONE_ID: WhatsApp Phone ID (optional)
WHATSAPP_VERIFY_TOKEN: Webhook verification token (optional)
Installation
Clone the repository:
git clone https://github.com/yourusername/ramadan-habit-tracker.git
cd ramadan-habit-tracker
Install dependencies:
pip install -r requirements.txt
Run the bot:
python main.py
Usage
Telegram Commands
/start - Start or restart the bot
/log - Log your daily Ramadan habits
/progress - View your progress
/history - View past day logs
/leaderboard - See the top performers
/export - Export your data as CSV
/help - Show available commands
WhatsApp Commands
start or hi - Start the bot
log - Log your daily Ramadan habits
progress - View your progress
leaderboard - See the top performers
history - View past day logs
Admin Commands (Telegram)
/users - View all users data
/database - Database statistics
/exportall - Export all users' data
/resetdatabase - Reset all database data
Project Structure
main.py - Entry point and server for both bots
bot.py - Telegram bot implementation
whatsapp_bot.py - WhatsApp bot implementation
database.py - SQLite database handler
reminders.py - Daily reminder scheduler
sheets.py - Google Sheets integration (optional)
Tech Stack
Python
Telebot (Telegram API)
WhatsApp Business API
SQLite
Flask (for webhook)
License
This project is available for personal use.

Creator
Made with ❤️ by HBK

May Allah accept all your worship and make this Ramadan your most rewarding one yet! 🤲
