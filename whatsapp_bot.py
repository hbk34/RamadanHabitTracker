
import os
import requests
import json
import datetime
import pytz
from hijri_converter import Gregorian
from database import Database

# Initialize database
db = Database()

# WhatsApp Business Platform credentials
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN")
WHATSAPP_PHONE_ID = os.environ.get("WHATSAPP_PHONE_ID")

# Predefined goals (same as in the Telegram bot)
GOALS = {
    "prayer": "5 times a day",
    "taraweeh": 30,
    "quran": "600 pages",
    "quran_meal": "90 pages",
    "tahajjud": 30
}

def send_whatsapp_message(phone_number, message):
    """Send a WhatsApp message to a specific phone number"""
    url = f"https://graph.facebook.com/v17.0/{WHATSAPP_PHONE_ID}/messages"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {WHATSAPP_TOKEN}"
    }
    
    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": phone_number,
        "type": "text",
        "text": {
            "body": message
        }
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(data))
    return response.json()

def send_interactive_buttons(phone_number, message, buttons):
    """Send interactive buttons to the user"""
    url = f"https://graph.facebook.com/v17.0/{WHATSAPP_PHONE_ID}/messages"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {WHATSAPP_TOKEN}"
    }
    
    button_items = []
    for button_text in buttons:
        button_items.append({
            "type": "reply",
            "reply": {
                "id": button_text.lower().replace(" ", "_"),
                "title": button_text
            }
        })
    
    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": phone_number,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
                "text": message
            },
            "action": {
                "buttons": button_items
            }
        }
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(data))
    return response.json()

def handle_start(phone_number, name=None):
    """Handle the start command"""
    today = datetime.datetime.now()
    gregorian_date = today.strftime("%d %B %Y")
    
    # Convert to Hijri
    hijri_date = Gregorian(today.year, today.month, today.day).to_hijri()
    hijri_formatted = f"{hijri_date.day} {hijri_date.month_name()} {hijri_date.year}H"
    
    date_info = f"📅 Today is {gregorian_date}\n📅 {hijri_formatted}"
    
    # Introduction message (limited to WhatsApp message size limits)
    intro_message = (
        "🌙 *Welcome to the Ramadan Habit Tracker!* 🌙\n\n"
        "Assalamu alaikum! This bot helps you track your daily worship during Ramadan.\n\n"
        "✨ *Features:*\n"
        "• Track 5 daily prayers\n"
        "• Record Quran and translation reading (pages)\n"
        "• Log Taraweeh and Tahajjud\n"
        "• View progress and leaderboard\n\n"
        "📱 *Commands:*\n"
        "Type 'log' - Record activities\n"
        "Type 'progress' - Check stats\n"
        "Type 'leaderboard' - Compare with others\n\n"
        "Daily reminders at 8 PM. May Allah accept your worship! 🤲\n\n"
    )
    
    admin_id = "YOUR_WHATSAPP_NUMBER"  # Your WhatsApp number with country code
    
    if not name:
        # Get or create user in database
        name = db.get_user_name(phone_number)
        if not name:
            # Add new user
            name = f"User_{phone_number[-4:]}"  # Use last 4 digits as identifier
            db.add_user(phone_number, name)
    
    # Full message with goals
    full_message = f"{intro_message}\n{date_info}\n\nYour goals:\n{display_goals()}"
    
    # Send message to user
    send_whatsapp_message(phone_number, full_message)
    
    # Send interactive buttons for main actions
    send_interactive_buttons(
        phone_number,
        "What would you like to do?",
        ["Log Habit", "Check Progress", "View Leaderboard"]
    )

def display_goals():
    """Generate a string with the goals"""
    goal_string = ""
    for goal, target in GOALS.items():
        goal_string += f"- {goal.capitalize()}: {target}\n"
    goal_string += "\nThis bot was made by hbk"
    return goal_string

def handle_log(phone_number):
    """Handle the log command"""
    name = db.get_user_name(phone_number)
    
    if not name:
        # Add new user if not exists
        name = f"User_{phone_number[-4:]}"
        db.add_user(phone_number, name)
    
    # Send habit selection buttons
    buttons = [g.capitalize() for g in GOALS]
    send_interactive_buttons(
        phone_number,
        "What would you like to log today?",
        buttons
    )

def handle_progress(phone_number):
    """Handle the progress command"""
    name = db.get_user_name(phone_number)
    
    if not name:
        name = f"User {phone_number}"
    
    progress_report = f"{name}'s Ramadan Progress:\n"
    
    # Prayer (daily goal)
    today_prayers = db.get_today_habit_count(phone_number, "prayer")
    progress_report += f"Prayer: {today_prayers}/5 (today)\n"
    
    # Taraweeh & Tahajjud 
    for goal in ["taraweeh", "tahajjud"]:
        today_completed = db.get_today_habit_count(phone_number, goal)
        days_completed = db.get_habit_days(phone_number, goal)
        target = GOALS[goal]
        progress_report += f"{goal.capitalize()}: {today_completed}/1 (today), {days_completed}/{target} times total\n"
    
    # Quran goals
    for goal in ["quran", "quran_meal"]:
        total = db.get_habit_count(phone_number, goal)
        target = GOALS[goal]
        progress_report += f"{goal.replace('_', ' ').capitalize()}: {total}/{target}\n"
    
    send_whatsapp_message(phone_number, progress_report)

def handle_leaderboard(phone_number):
    """Handle the leaderboard command"""
    leaderboard_text = "🏆 Ramadan Leaderboard 🏆\n\n"
    
    # List of habits to show leaderboards for
    habits = ["prayer", "taraweeh", "tahajjud", "quran", "quran_meal"]
    
    for habit in habits:
        # Get leaderboard data for this specific habit
        habit_data = db.get_habit_leaderboard(habit)
        
        # Format the habit name nicely
        habit_name = habit.replace("_", " ").capitalize()
        
        leaderboard_text += f"📊 {habit_name} Leaderboard:\n"
        
        if not habit_data:
            leaderboard_text += "No entries yet.\n\n"
            continue
        
        # Show top 5 users for each habit to keep the message concise
        rank = 1
        for user_id, name, count in habit_data[:5]:
            # For Quran habits, show "pages" in the display
            if habit in ["quran", "quran_meal"]:
                leaderboard_text += f"{rank}. {name}: {count} pages\n"
            # For Taraweeh and Tahajjud, show "times"
            elif habit in ["taraweeh", "tahajjud"]:
                leaderboard_text += f"{rank}. {name}: {count} times\n"
            # For prayers, just show count
            else:
                leaderboard_text += f"{rank}. {name}: {count} prayers\n"
            rank += 1
        
        leaderboard_text += "\n"
    
    send_whatsapp_message(phone_number, leaderboard_text)
    
def handle_history(phone_number):
    """Handle the history command for WhatsApp"""
    name = db.get_user_name(phone_number)
    
    if not name:
        send_whatsapp_message(phone_number, "Please start by sending 'start'.")
        return
    
    # Send options as buttons
    send_interactive_buttons(
        phone_number,
        "Please select an option:",
        ["Yesterday", "Last 7 days", "Specific date"]
    )
    
def show_date_history_whatsapp(phone_number, days_ago=1):
    """Show habit history for a specific number of days ago for WhatsApp"""
    eastern = pytz.timezone('US/Eastern')
    target_date = (datetime.datetime.now(eastern) - datetime.timedelta(days=days_ago)).strftime("%Y-%m-%d")
    
    show_specific_date_history_whatsapp(phone_number, target_date)

def show_specific_date_history_whatsapp(phone_number, date_string):
    """Show habit history for a specific date for WhatsApp"""
    # Get user's name
    name = db.get_user_name(phone_number)
    
    # Format the date nicely for display
    try:
        date_obj = datetime.datetime.strptime(date_string, "%Y-%m-%d")
        formatted_date = date_obj.strftime("%B %d, %Y")
    except ValueError:
        formatted_date = date_string
    
    # Get habits for that specific date
    user_habits = db.get_user_habits_for_date(phone_number, date_string)
    
    if not user_habits:
        send_whatsapp_message(phone_number, f"No habits were logged on {formatted_date}.")
        return
    
    # Build the report
    report = f"📋 *{name}'s Habits on {formatted_date}*\n\n"
    
    for habit_name, count in user_habits:
        # Format habit name
        display_name = habit_name.replace("_", " ").capitalize()
        
        # Format count based on habit type
        if habit_name in ["quran", "quran_meal"]:
            report += f"• {display_name}: {count} pages\n"
        elif habit_name in ["taraweeh", "tahajjud"]:
            report += f"• {display_name}: {'Yes' if count > 0 else 'No'}\n"
        elif habit_name == "prayer":
            report += f"• {display_name}: {count}/5\n"
        else:
            report += f"• {display_name}: {count}\n"
    
    send_whatsapp_message(phone_number, report)

def show_weekly_summary_whatsapp(phone_number):
    """Show a summary of habits for the last 7 days for WhatsApp"""
    name = db.get_user_name(phone_number)
    eastern = pytz.timezone('US/Eastern')
    today = datetime.datetime.now(eastern)
    
    report = f"📊 *{name}'s Last 7 Days Summary*\n\n"
    
    # Loop through the last 7 days
    has_data = False
    for days_ago in range(6, -1, -1):
        target_date = (today - datetime.timedelta(days=days_ago)).strftime("%Y-%m-%d")
        formatted_date = (today - datetime.timedelta(days=days_ago)).strftime("%a, %b %d")
        
        # Get habits for this date
        user_habits = db.get_user_habits_for_date(phone_number, target_date)
        
        if user_habits:
            has_data = True
            report += f"*{formatted_date}*\n"
            
            for habit_name, count in user_habits:
                # Format habit name and count
                display_name = habit_name.replace("_", " ").capitalize()
                
                if habit_name in ["quran", "quran_meal"]:
                    report += f"• {display_name}: {count} pages\n"
                elif habit_name in ["taraweeh", "tahajjud"]:
                    report += f"• {display_name}: {'Yes' if count > 0 else 'No'}\n"
                elif habit_name == "prayer":
                    report += f"• {display_name}: {count}/5\n"
                else:
                    report += f"• {display_name}: {count}\n"
            
            report += "\n"
    
    if not has_data:
        report = f"No habits were logged in the last 7 days."
    
    send_whatsapp_message(phone_number, report)

def process_webhook(data):
    """Process incoming webhook data from WhatsApp"""
    try:
        # Extract the message details
        entry = data['entry'][0]
        changes = entry['changes'][0]
        value = changes['value']
        
        if 'messages' not in value:
            return "No messages found"
        
        message = value['messages'][0]
        phone_number = message['from']
        
        # Check if it's a text message
        if message['type'] == 'text':
            text = message['text']['body'].lower()
            
            # Handle commands
            if text in ['start', 'hi', 'hello', 'assalamualaikum', 'salam']:
                handle_start(phone_number)
            elif text == 'log':
                handle_log(phone_number)
            elif text == 'progress':
                handle_progress(phone_number)
            elif text == 'leaderboard':
                handle_leaderboard(phone_number)
            elif text == 'history':
                handle_history(phone_number)
            elif text == 'yesterday':
                show_date_history_whatsapp(phone_number, days_ago=1)
            elif text == 'last 7 days':
                show_weekly_summary_whatsapp(phone_number)
            elif text.startswith('date:'):
                # Format should be 'date:YYYY-MM-DD'
                try:
                    date_part = text.split(':', 1)[1].strip()
                    # Validate date format
                    datetime.datetime.strptime(date_part, "%Y-%m-%d")
                    show_specific_date_history_whatsapp(phone_number, date_part)
                except (ValueError, IndexError):
                    send_whatsapp_message(phone_number, "Invalid date format. Please use date:YYYY-MM-DD (e.g., date:2024-03-15)")
            # Handle direct habit logging
            elif text in [h for h in GOALS]:
                # This is a habit name, handle it
                process_habit_selection(phone_number, text)
            elif text.isdigit() and 1 <= int(text) <= 999:
                # This is likely a response to a page count or prayer count question
                # You'd need to track the conversation state to know which habit this applies to
                # For simplicity, we'll just acknowledge the message here
                send_whatsapp_message(phone_number, f"Received {text}. Please use the full command format.")
            else:
                # Default response
                send_whatsapp_message(
                    phone_number, 
                    "I didn't understand that command. Available commands:\n- start\n- log\n- progress\n- leaderboard\n- history"
                )
        
        # Handle interactive message responses (button clicks)
        elif message['type'] == 'interactive':
            if message['interactive']['type'] == 'button_reply':
                button_id = message['interactive']['button_reply']['id']
                
                if button_id == 'log_habit':
                    handle_log(phone_number)
                elif button_id == 'check_progress':
                    handle_progress(phone_number)
                elif button_id == 'view_leaderboard':
                    handle_leaderboard(phone_number)
                elif button_id in [h.lower() for h in GOALS]:
                    # This is a habit selection from buttons
                    process_habit_selection(phone_number, button_id)
        
        return "Processed successfully"
    
    except Exception as e:
        print(f"Error processing webhook: {e}")
        return f"Error: {str(e)}"

def process_habit_selection(phone_number, habit):
    """Process a selected habit for logging"""
    # Convert button_id to habit name if needed
    habit = habit.lower()
    
    # Handle different types of goals
    if habit == "prayer":
        # For regular prayers, ask for the number
        buttons = [str(i) for i in range(1, 6)]  # Options 1-5
        send_interactive_buttons(
            phone_number,
            "How many prayers did you perform? (1-5)",
            buttons
        )
    elif habit in ["taraweeh", "tahajjud"]:
        # For taraweeh and tahajjud, ask yes/no
        send_interactive_buttons(
            phone_number,
            f"Did you perform {habit.capitalize()} prayer today?",
            ["Yes", "No"]
        )
    elif habit in ["quran", "quran_meal"]:
        # For Quran reading, give some common page count options
        common_pages = ["1", "3", "5", "10", "20"]
        send_interactive_buttons(
            phone_number,
            f"How many pages of {habit.replace('_', ' ')} did you read today?",
            common_pages + ["Other"]
        )
    
    # Note: In a full implementation, you would need to track conversation 
    # state to know what the next number response applies to.
