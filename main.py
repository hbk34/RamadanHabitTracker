
# Import and run the Telegram and WhatsApp bots
import telebot
from telebot.types import BotCommand
from bot import bot
import time
import threading
import os
from flask import Flask, request, jsonify

# For WhatsApp integration
from whatsapp_bot import process_webhook

# Create Flask app for health checks and webhooks
app = Flask(__name__)

@app.route('/')
def index():
    return "Ramadan Habit Tracker Bot is running!"

# WhatsApp webhook verification
@app.route('/whatsapp/webhook', methods=['GET'])
def verify_webhook():
    # WhatsApp verification
    verify_token = os.environ.get("WHATSAPP_VERIFY_TOKEN", "your_verification_token")
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    
    if mode and token:
        if mode == "subscribe" and token == verify_token:
            print("Webhook verified!")
            return challenge, 200
        else:
            return "Verification failed", 403
    return "Hello World", 200

# WhatsApp webhook for receiving messages
@app.route('/whatsapp/webhook', methods=['POST'])
def receive_message():
    try:
        data = request.get_json()
        print("Received webhook data:", data)
        
        # Process the webhook data
        result = process_webhook(data)
        
        return jsonify({"status": "success", "message": result}), 200
    except Exception as e:
        print(f"Error handling webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

def run_telegram_bot():
    print("Starting Ramadan Habit Tracker Telegram Bot...")
    # Remove webhook to ensure polling works correctly
    bot.remove_webhook()
    time.sleep(1)  # Give it time to remove the webhook
    
    try:
        # Set up commands to display in the menu
        commands = [
            BotCommand("start", "Start or restart the bot"),
            BotCommand("log", "Log your daily Ramadan habits"),
            BotCommand("progress", "View your progress"),
            BotCommand("history", "View past day logs"),
            BotCommand("leaderboard", "See the top performers"),
            BotCommand("export", "Export your data as CSV"),
            BotCommand("help", "Show available commands")
        ]
        bot.set_my_commands(commands)
        print("Command menu configured successfully")
    except Exception as e:
        print(f"Error configuring command menu: {e}")
    
    # Start polling with error handling
    while True:
        try:
            print("Telegram Bot is now listening for messages...")
            bot.polling(none_stop=True, interval=0, timeout=20)
        except telebot.apihelper.ApiException as e:
            print(f"ApiException error: {e}")
            time.sleep(5)
        except Exception as e:
            print(f"Unexpected error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    # Check which platform(s) to run
    run_telegram = os.environ.get("RUN_TELEGRAM", "true").lower() == "true"
    run_whatsapp = os.environ.get("RUN_WHATSAPP", "true").lower() == "true"
    
    if run_telegram:
        # Start the Telegram bot in a separate thread
        telegram_thread = threading.Thread(target=run_telegram_bot)
        telegram_thread.daemon = True
        telegram_thread.start()
    
    # Start the daily reminder scheduler
    from reminders import start_reminder_thread
    start_reminder_thread()
    
    # Run the Flask app (needed for WhatsApp webhook and health checks)
    print("Starting HTTP server...")
    app.run(host="0.0.0.0", port=8080)
