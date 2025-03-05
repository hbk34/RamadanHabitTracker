
import time
import datetime
import pytz
import threading
from database import Database
from whatsapp_bot import send_whatsapp_message
from bot import bot  # Telegram bot

# Initialize database
db = Database()

def send_daily_reminders():
    """Send daily reminders to users at 8 PM Eastern Time"""
    # Use Eastern time zone
    eastern = pytz.timezone('US/Eastern')
    
    while True:
        now = datetime.datetime.now(eastern)
        
        # Check if it's 8 PM
        if now.hour == 20 and now.minute == 0:
            print(f"Sending daily reminders at {now}")
            
            # Get all users
            users = db.get_all_users()
            
            reminder_message = "🌙 Ramadan Reminder 🌙\n\nDon't forget to log your good deeds for today! Use the 'log' command to record your progress."
            
            # Send to each user
            for user_id, name in users:
                try:
                    # Check if it's a WhatsApp number (starts with +)
                    if str(user_id).startswith('+'):
                        # Send WhatsApp message
                        send_whatsapp_message(user_id, reminder_message)
                    else:
                        # Send Telegram message
                        bot.send_message(user_id, reminder_message)
                    print(f"Sent reminder to {name} ({user_id})")
                except Exception as e:
                    print(f"Failed to send reminder to {name} ({user_id}): {e}")
            
            # Wait for a minute to avoid sending multiple reminders
            time.sleep(60)
        
        # Check every minute
        time.sleep(60)

# Start the reminder thread
def start_reminder_thread():
    reminder_thread = threading.Thread(target=send_daily_reminders)
    reminder_thread.daemon = True
    reminder_thread.start()
    print("Daily reminder scheduler started")
