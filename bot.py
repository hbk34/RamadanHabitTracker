import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, BotCommand
import datetime
import pytz
from database import Database

# Replace this with your bot token from BotFather
BOT_TOKEN = "7717721582:AAG4zRMwqK_2RXZiRSf5CSz9T8q-vTdxpss"
bot = telebot.TeleBot(BOT_TOKEN)

# Initialize database
db = Database()

# Predefined goals
GOALS = {
    "prayer": "5 times a day" ,  # 5 prayers per day
    "taraweeh": 30,  # 30 days of Ramadan
    "quran": "600 pages",  # in pages
    "quran_meal": "90 pages",  # in pages
    "tahajjud": 30  # 30 days of Ramadan
}

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    name = db.get_user_name(user_id)

    # Get current date in Gregorian and Hijri calendars
    import datetime
    from hijri_converter import Gregorian

    today = datetime.datetime.now()
    gregorian_date = today.strftime("%d %B %Y")

    # Convert to Hijri
    hijri_date = Gregorian(today.year, today.month, today.day).to_hijri()
    hijri_formatted = f"{hijri_date.day} {hijri_date.month_name()} {hijri_date.year}H"

    date_info = f"📅 Today is {gregorian_date}\n📅 {hijri_formatted}"
    
    # Introduction message
    intro_message = (
        "🌙 *Welcome to the Ramadan Habit Tracker Bot!* 🌙\n\n"
        "Assalamu alaikum and Ramadan Mubarak!\n\n"
        "This Telegram bot is designed to help you make the most of this blessed month by tracking your daily Islamic practices. Stay consistent, measure your progress, and strengthen your worship during Ramadan.\n\n"
        "✨ *Features:*\n"
        "• Track your five daily prayers\n"
        "• Record your Quran recitation and Quran Meal (translation) reading in pages\n"
        "• Log your Taraweeh and Tahajjud prayers\n"
        "• View your personal progress throughout Ramadan\n"
        "• Compare your efforts with others on the leaderboard\n"
        "• Export your data to keep a record of your journey\n\n"
        "📱 *Getting Started:*\n"
        "1. Use /log to record your daily activities\n"
        "2. Check your progress with /progress\n"
        "3. See how you rank on the /leaderboard\n\n"
        "You'll receive daily reminders at 8 PM to help you stay consistent with logging your deeds.\n\n"
        "May Allah accept all your worship and make this Ramadan your most rewarding one yet! 🤲\n\n"
        "Remember: The purpose of tracking is to encourage consistency, not to create a burden. Do your best and Allah SWT knows your intentions.\n\n"
    )

    # Admin ID check
    admin_id = 5861883539  # Your Telegram ID

    # List of available commands - show different commands based on user role
    if user_id == admin_id:
        # Admin commands
        commands = (
            "Available commands:\n"
            "/start - Start or restart the bot\n"
            "/log - Log your daily Ramadan habits\n"
            "/progress - View your progress\n"
            "/leaderboard - See the top performers\n"
            "/export - Export your data as CSV\n"
            "/users - View all users data\n"
            "/database - Database statistics\n"
            "/exportall - Export all users' data\n"
            "/synctosheets - Sync data to Google Sheets\n"
            "/debugsheets - Check Google Sheets integration\n"
            "/setupsheets - Get help setting up Google Sheets\n"
            "/help - Show available commands"
        )
    else:
        # Regular user commands
        commands = (
            "Available commands:\n"
            "/start - Start or restart the bot\n"
            "/log - Log your daily Ramadan habits\n"
            "/progress - View your progress\n"
            "/leaderboard - See the top performers\n"
            "/export - Export your data as CSV\n"
            "/help - Show available commands"
        )

    if not name:
        # Get user's name from Telegram profile
        first_name = message.from_user.first_name
        last_name = message.from_user.last_name or ""
        username = message.from_user.username

        # Use full name if available, otherwise username
        if first_name or last_name:
            name = f"{first_name} {last_name}".strip()
        elif username:
            name = username
        else:
            name = f"User_{user_id}"  # Fallback if no name information available

        # Save the name to database
        db.add_user(user_id, name)
        bot.send_message(user_id, intro_message + f"{date_info}\n\nHere are your goals:\n{display_goals()}\n\n{commands}", parse_mode="Markdown")
    else:
        bot.send_message(user_id, f"Welcome back, {name}!\n\n{date_info}\n\nHere are your goals:\n{display_goals()}\n\n{commands}")

def display_goals():
    goal_string = ""
    for goal, target in GOALS.items():
        goal_string += f"- {goal.capitalize()}: {target}\n"
    goal_string += "\nThis bot was made by hbk"
    return goal_string

@bot.message_handler(commands=['log'])
def log(message):
    user_id = message.chat.id
    name = db.get_user_name(user_id)

    if not name:
        # Similar logic to start command - get user's name from Telegram
        first_name = message.from_user.first_name
        last_name = message.from_user.last_name or ""
        username = message.from_user.username

        if first_name or last_name:
            name = f"{first_name} {last_name}".strip()
        elif username:
            name = username
        else:
            name = f"User_{user_id}"

        db.add_user(user_id, name)

    markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    buttons = [KeyboardButton(g.capitalize()) for g in GOALS]
    markup.add(*buttons)
    bot.send_message(user_id, "What would you like to log today?", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text.lower() in GOALS)
def handle_goal_selection(message):
    user_id = message.chat.id
    goal = message.text.lower()

    # Handle different types of goals
    if goal == "prayer":
        # For regular prayers, ask for the number
        markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        buttons = [KeyboardButton(str(i)) for i in range(1, 6)]  # Options 1-5
        markup.add(*buttons)
        msg = bot.send_message(user_id, "How many prayers did you perform? (1-5)", reply_markup=markup)
        bot.register_next_step_handler(msg, process_prayer_count, goal)
    elif goal in ["taraweeh", "tahajjud"]:
        # For taraweeh and tahajjud, ask yes/no
        markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add(KeyboardButton("Yes"), KeyboardButton("No"))
        msg = bot.send_message(user_id, f"Did you perform {goal.capitalize()} prayer today?", reply_markup=markup)
        bot.register_next_step_handler(msg, process_yes_no_prayer, goal)
    elif goal == "quran":
        # For Quran, create a dropdown with pages 1-999
        markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        # First row: common values
        common_pages = ["1", "3", "5", "10", "20"]
        markup.add(*[KeyboardButton(p) for p in common_pages])
        # Add some range options in rows
        ranges = [["30", "50", "100"], ["150", "200", "300"], ["400", "500", "600"], ["700", "800", "900"]]
        for row in ranges:
            markup.add(*[KeyboardButton(p) for p in row])
        # Add "Other" option
        markup.add(KeyboardButton("Other"))
        msg = bot.send_message(user_id, "Select or enter how many pages of Quran did you read (1-999):", reply_markup=markup)
        bot.register_next_step_handler(msg, process_quran_pages, goal)
    elif goal == "quran_meal":
        # For Quran meal, create a dropdown with pages 1-999
        markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        # First row: common values
        common_pages = ["1", "3", "5", "10", "20"]
        markup.add(*[KeyboardButton(p) for p in common_pages])
        # Add some range options in rows
        ranges = [["30", "50", "100"], ["150", "200", "300"], ["400", "500", "600"], ["700", "800", "900"]]
        for row in ranges:
            markup.add(*[KeyboardButton(p) for p in row])
        # Add "Other" option
        markup.add(KeyboardButton("Other"))
        msg = bot.send_message(user_id, "Select or enter how many pages of Quran translation did you read (1-999):", reply_markup=markup)
        bot.register_next_step_handler(msg, process_quran_pages, goal)
    else:
        # For any other goals, just increment by 1
        db.log_habit(user_id, goal)
        progress = db.get_habit_count(user_id, goal)
        goal_target = GOALS[goal]
        bot.send_message(user_id, f"✅ {goal.capitalize()} logged! Progress: {progress}/{goal_target}")
        ask_log_more(user_id)

def process_quran_pages(message, goal):
    user_id = message.chat.id
    response = message.text.strip()

    # Handle the "Other" option
    if response.lower() == "other":
        msg = bot.send_message(user_id, "Please enter the number of pages (1-999):")
        bot.register_next_step_handler(msg, process_custom_quran_pages, goal)
        return

    try:
        # Try to convert input to integer
        pages = int(response)
        if 1 <= pages <= 999:
            # Check if already logged today
            today_count = db.get_today_habit_count(user_id, goal)

            if today_count > 0:
                # Ask if user wants to add or replace the count
                markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
                markup.add(KeyboardButton("Add"), KeyboardButton("Replace"), KeyboardButton("Cancel"))
                msg = bot.send_message(
                    user_id, 
                    f"You've already logged {today_count} pages of {goal.replace('_', ' ')} today. "
                    f"Do you want to add {pages} pages (total: {today_count + pages}) or replace with {pages} pages?",
                    reply_markup=markup
                )
                bot.register_next_step_handler(msg, confirm_update_pages, goal, pages, today_count)
            else:
                # Log the new pages
                db.log_habit(user_id, goal, pages)
                total_pages = db.get_habit_count(user_id, goal)
                goal_target = GOALS[goal]
                goal_name = goal.replace('_', ' ').capitalize()

                # Now display progress directly in pages for Quran
                bot.send_message(
                    user_id, 
                    f"✅ {pages} pages of {goal_name} logged! Total progress: {total_pages}/{goal_target} pages"
                )
                ask_log_more(user_id)
        else:
            msg = bot.send_message(user_id, "Please enter a number between 1 and 999:")
            bot.register_next_step_handler(msg, process_quran_pages, goal)
    except ValueError:
        msg = bot.send_message(user_id, "Please enter a valid number between 1 and 999:")
        bot.register_next_step_handler(msg, process_quran_pages, goal)

def process_custom_quran_pages(message, goal):
    user_id = message.chat.id
    try:
        pages = int(message.text.strip())
        if 1 <= pages <= 999:
            # Check if already logged today
            today_count = db.get_today_habit_count(user_id, goal)

            if today_count > 0:
                # Ask if user wants to add or replace the count
                markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
                markup.add(KeyboardButton("Add"), KeyboardButton("Replace"), KeyboardButton("Cancel"))
                msg = bot.send_message(
                    user_id, 
                    f"You've already logged {today_count} pages of {goal.replace('_', ' ')} today. "
                    f"Do you want to add {pages} pages (total: {today_count + pages}) or replace with {pages} pages?",
                    reply_markup=markup
                )
                bot.register_next_step_handler(msg, confirm_update_pages, goal, pages, today_count)
            else:
                # Log the new pages
                db.log_habit(user_id, goal, pages)
                total_pages = db.get_habit_count(user_id, goal)
                goal_target = GOALS[goal]
                goal_name = goal.replace('_', ' ').capitalize()

                # Now display progress directly in pages for Quran
                bot.send_message(
                    user_id, 
                    f"✅ {pages} pages of {goal_name} logged! Total progress: {total_pages}/{goal_target} pages"
                )
                ask_log_more(user_id)
        else:
            msg = bot.send_message(user_id, "Please enter a number between 1 and 999:")
            bot.register_next_step_handler(msg, process_custom_quran_pages, goal)
    except ValueError:
        msg = bot.send_message(user_id, "Please enter a valid number between 1 and 999:")
        bot.register_next_step_handler(msg, process_custom_quran_pages, goal)

def confirm_update_pages(message, goal, new_pages, previous_count):
    user_id = message.chat.id
    response = message.text.lower()

    if response == "add":
        # Add to existing log for today
        updated_count = previous_count + new_pages
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        db.cursor.execute(
            "UPDATE habits SET count = ? WHERE user_id = ? AND habit_name = ? AND date = ?",
            (updated_count, user_id, goal, today)
        )
        db.conn.commit()

        total_pages = db.get_habit_count(user_id, goal)
        goal_target = GOALS[goal]
        goal_name = goal.replace('_', ' ').capitalize()
        bot.send_message(
            user_id,
            f"✅ Added {new_pages} pages of {goal_name}! Total progress: {total_pages}/{goal_target}"
        )
    elif response == "replace":
        # Update existing log for today
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        db.cursor.execute(
            "UPDATE habits SET count = ? WHERE user_id = ? AND habit_name = ? AND date = ?",
            (new_pages, user_id, goal, today)
        )
        db.conn.commit()

        total_pages = db.get_habit_count(user_id, goal)
        goal_target = GOALS[goal]
        goal_name = goal.replace('_', ' ').capitalize()
        bot.send_message(
            user_id,
            f"✅ Replaced with {new_pages} pages of {goal_name}! Total progress: {total_pages}/{goal_target}"
        )
    elif response == "cancel":
        bot.send_message(user_id, "Log update canceled.")
    else:
        bot.send_message(user_id, "Invalid option selected. Please choose Add, Replace, or Cancel.")


    ask_log_more(user_id)

def process_prayer_count(message, goal):
    user_id = message.chat.id
    try:
        count = int(message.text)
        if 1 <= count <= 5:
            # Check if already logged today
            today_count = db.get_today_habit_count(user_id, "prayer")

            if today_count > 0:
                # Ask for confirmation if updating existing log
                markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
                markup.add(KeyboardButton("Yes"), KeyboardButton("No"))
                msg = bot.send_message(
                    user_id, 
                    f"You've already logged {today_count} prayers today. Do you want to update it to {count} prayers?",
                    reply_markup=markup
                )
                bot.register_next_step_handler(msg, confirm_update_prayers, count)
            else:
                # For prayers, we set the exact count for today
                db.set_prayer_count(user_id, count)

                # Get today's prayer count
                today_count = db.get_today_habit_count(user_id, "prayer")
                bot.send_message(user_id, f"✅ {count} prayer(s) logged! Daily progress: {today_count}/5")
                ask_log_more(user_id)
        else:
            bot.send_message(user_id, "Please enter a number between 1 and 5.")
            return
    except ValueError:
        bot.send_message(user_id, "Please enter a valid number between 1 and 5.")

def confirm_update_prayers(message, new_count):
    user_id = message.chat.id
    response = message.text.lower()

    if response == "yes":
        # Update existing log for today
        db.set_prayer_count(user_id, new_count)
        today_count = db.get_today_habit_count(user_id, "prayer")
        bot.send_message(user_id, f"✅ Updated to {new_count} prayer(s)! Daily progress: {today_count}/5")
    else:
        bot.send_message(user_id, "Prayer log update canceled.")

    ask_log_more(user_id)

def ask_log_more(user_id):
    """Ask if the user wants to log more habits"""
    markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(KeyboardButton("Yes"), KeyboardButton("No"))
    msg = bot.send_message(
        user_id, 
        "Would you like to log another habit?",
        reply_markup=markup
    )
    bot.register_next_step_handler(msg, process_log_more)

def process_log_more(message):
    user_id = message.chat.id
    response = message.text.lower()

    if response == "yes":
        log(message)  # Call the log function to start the logging process again
    else:
        bot.send_message(user_id, "Great job with your tracking! Use /progress to check your overall progress.")

def process_yes_no_prayer(message, goal):
    user_id = message.chat.id
    response = message.text.lower()

    if response == "yes":
        # Check if already logged today
        today_count = db.get_today_habit_count(user_id, goal)
        if today_count > 0:
            bot.send_message(user_id, f"You have already logged {goal.capitalize()} prayer for today.")
            ask_log_more(user_id)
        else:
            db.log_habit(user_id, goal)
            days_logged = db.get_habit_days(user_id, goal)
            goal_target = GOALS[goal]
            bot.send_message(user_id, f"✅ {goal.capitalize()} prayer logged! Progress: {days_logged}/{goal_target} days")
            ask_log_more(user_id)
    elif response == "no":
        bot.send_message(user_id, f"No problem! You can log your {goal.capitalize()} prayer tomorrow.")
        ask_log_more(user_id)
    else:
        markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add(KeyboardButton("Yes"), KeyboardButton("No"))
        msg = bot.send_message(user_id, f"Please answer with Yes or No. Did you perform {goal.capitalize()} prayer today?", reply_markup=markup)
        bot.register_next_step_handler(msg, process_yes_no_prayer, goal)

@bot.message_handler(commands=['progress'])
def progress(message):
    user_id = message.chat.id
    name = db.get_user_name(user_id)

    if not name:
        name = f"User {user_id}"

    progress_report = f"{name}'s Ramadan Progress:\n"

    # Prayer (daily goal)
    today_prayers = db.get_today_habit_count(user_id, "prayer")
    progress_report += f"Prayer: {today_prayers}/5 (today)\n"

    # Taraweeh & Tahajjud (days completed - these reset daily)
    for goal in ["taraweeh", "tahajjud"]:
        today_completed = db.get_today_habit_count(user_id, goal)
        days_completed = db.get_habit_days(user_id, goal)
        target = GOALS[goal]
        progress_report += f"{goal.capitalize()}: {today_completed}/1 (today), {days_completed}/{target} days total\n"

    # Quran goals (cumulative progress - these don't reset daily)
    for goal in ["quran", "quran_meal"]:
        total = db.get_habit_count(user_id, goal)
        target = GOALS[goal]
        progress_report += f"{goal.replace('_', ' ').capitalize()}: {total}/{target}\n"

    bot.send_message(user_id, progress_report)

@bot.message_handler(commands=['leaderboard'])
def leaderboard(message):
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

    bot.send_message(message.chat.id, leaderboard_text)

@bot.message_handler(commands=['history'])
def history(message):
    user_id = message.chat.id
    name = db.get_user_name(user_id)

    if not name:
        bot.send_message(user_id, "Please start by using /start command and providing your name.")
        return
    
    bot.send_message(user_id, "Please select an option:", reply_markup=get_history_options())

def get_history_options():
    markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(KeyboardButton("Yesterday"))
    markup.add(KeyboardButton("Last 7 days"))
    markup.add(KeyboardButton("Specific date"))
    return markup

@bot.message_handler(func=lambda message: message.text in ["Yesterday", "Last 7 days", "Specific date"])
def handle_history_selection(message):
    user_id = message.chat.id
    option = message.text
    
    if option == "Yesterday":
        show_date_history(user_id, days_ago=1)
    elif option == "Last 7 days":
        show_weekly_summary(user_id)
    elif option == "Specific date":
        msg = bot.send_message(user_id, "Please enter a date in YYYY-MM-DD format (e.g., 2024-03-15):")
        bot.register_next_step_handler(msg, process_specific_date)

def process_specific_date(message):
    user_id = message.chat.id
    date_text = message.text.strip()
    
    # Validate date format
    try:
        # Parse the date to validate format
        specified_date = datetime.datetime.strptime(date_text, "%Y-%m-%d").date()
        today = datetime.datetime.now().date()
        
        # Check if date is in the past
        if specified_date > today:
            bot.send_message(user_id, "You cannot view logs for future dates. Please enter a valid past date.")
            return
            
        show_specific_date_history(user_id, date_text)
    except ValueError:
        bot.send_message(user_id, "Invalid date format. Please use YYYY-MM-DD format (e.g., 2024-03-15).")

def show_date_history(user_id, days_ago=1):
    """Show habit history for a specific number of days ago"""
    eastern = pytz.timezone('US/Eastern')
    target_date = (datetime.datetime.now(eastern) - datetime.timedelta(days=days_ago)).strftime("%Y-%m-%d")
    
    show_specific_date_history(user_id, target_date)

def show_specific_date_history(user_id, date_string):
    """Show habit history for a specific date"""
    # Get user's name
    name = db.get_user_name(user_id)
    
    # Format the date nicely for display
    try:
        date_obj = datetime.datetime.strptime(date_string, "%Y-%m-%d")
        formatted_date = date_obj.strftime("%B %d, %Y")
    except ValueError:
        formatted_date = date_string
    
    # Get habits for that specific date
    user_habits = db.get_user_habits_for_date(user_id, date_string)
    
    if not user_habits:
        bot.send_message(user_id, f"No habits were logged on {formatted_date}.")
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
    
    bot.send_message(user_id, report, parse_mode="Markdown")

def show_weekly_summary(user_id):
    """Show a summary of habits for the last 7 days"""
    name = db.get_user_name(user_id)
    eastern = pytz.timezone('US/Eastern')
    today = datetime.datetime.now(eastern)
    
    report = f"📊 *{name}'s Last 7 Days Summary*\n\n"
    
    # Loop through the last 7 days
    has_data = False
    for days_ago in range(6, -1, -1):
        target_date = (today - datetime.timedelta(days=days_ago)).strftime("%Y-%m-%d")
        formatted_date = (today - datetime.timedelta(days=days_ago)).strftime("%a, %b %d")
        
        # Get habits for this date
        user_habits = db.get_user_habits_for_date(user_id, target_date)
        
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
    
    bot.send_message(user_id, report, parse_mode="Markdown")

@bot.message_handler(commands=['users'])
def show_users(message):
    user_id = message.chat.id
    # Only show this to admin
    admin_id = 5861883539  # Your Telegram ID
    if user_id != admin_id:
        bot.send_message(user_id, "Sorry, this command is restricted to admin use only.")
        return

    users = db.get_all_users()
    if not users:
        bot.send_message(user_id, "No users in the database yet.")
        return

    user_list = "📊 Users in Database:\n\n"
    for u_id, u_name in users:
        user_list += f"User ID: {u_id}, Name: {u_name}\n"
        # Get some habit stats for this user
        prayer_count = db.get_habit_count(u_id, "prayer")
        taraweeh_days = db.get_habit_days(u_id, "taraweeh")
        quran_pages = db.get_habit_count(u_id, "quran")

        user_list += f"  - Prayers: {prayer_count}\n"
        user_list += f"  - Taraweeh days: {taraweeh_days}\n"
        user_list += f"  - Quran pages: {quran_pages}\n\n"

    # Split message if too long
    if len(user_list) > 4000:
        chunks = [user_list[i:i+4000] for i in range(0, len(user_list), 4000)]
        for chunk in chunks:
            bot.send_message(user_id, chunk)
    else:
        bot.send_message(user_id, user_list)

@bot.message_handler(commands=['database'])
def show_database_info(message):
    user_id = message.chat.id

    # Admin check
    admin_id = 5861883539  # Your Telegram ID
    if user_id != admin_id:
        bot.send_message(user_id, "Sorry, this command is restricted to admin use only.")
        return

    # Get database statistics
    users_count = len(db.get_all_users())

    # Count total habits logged
    db.cursor.execute("SELECT COUNT(*) FROM habits")
    habits_count = db.cursor.fetchone()[0]

    # Get date range
    db.cursor.execute("SELECT MIN(date), MAX(date) FROM habits")
    date_range = db.cursor.fetchone()
    min_date = date_range[0] if date_range and date_range[0] else "No data"
    max_date = date_range[1] if date_range and date_range[1] else "No data"

    db_info = f"📁 Database Information:\n\n"
    db_info += f"Total users: {users_count}\n"
    db_info += f"Total habit entries: {habits_count}\n"
    db_info += f"First entry date: {min_date}\n"
    db_info += f"Latest entry date: {max_date}\n"

    # Get habit counts by type
    habit_types = ["prayer", "taraweeh", "quran", "quran_translation", "tahajjud"]
    db_info += "\nEntries by habit type:\n"

    for habit in habit_types:
        db.cursor.execute("SELECT COUNT(*) FROM habits WHERE habit_name = ?", (habit,))
        count = db.cursor.fetchone()[0]
        db_info += f"- {habit.capitalize()}: {count} entries\n"

    bot.send_message(user_id, db_info)

# Bot will be started from main.py
# Don't start polling here
@bot.message_handler(commands=['export'])
def export_logs(message):
    user_id = message.chat.id
    name = db.get_user_name(user_id)

    if not name:
        bot.send_message(user_id, "Please start by using /start command first.")
        return

    # Generate CSV content
    csv_content = "Date,Habit,Count\n"
    habits = db.get_user_habits(user_id)

    if not habits:
        bot.send_message(user_id, "No habits logged yet.")
        return

    for date, habit_name, count in habits:
        csv_content += f"{date},{habit_name},{count}\n"

    # Create temporary file
    filename = f"ramadan_logs_{user_id}.csv"
    with open(filename, 'w') as f:
        f.write(csv_content)

    # Send the file
    with open(filename, 'rb') as f:
        bot.send_document(user_id, f, caption="Here are your Ramadan habit logs in CSV format.")

    # Clean up temporary file
    import os
    os.remove(filename)

    bot.send_message(user_id, "You can open this CSV file in Google Sheets or any spreadsheet program.")
@bot.message_handler(commands=['exportall'])
def export_all_logs(message):
    user_id = message.chat.id

    # Admin check - replace this with your actual Telegram user ID
    admin_id = 5861883539  # Your Telegram ID
    if user_id != admin_id:
        bot.send_message(user_id, "Sorry, this command is restricted to admin use only.")
        return

    # Generate CSV content with user information
    csv_content = "User ID,Name,Date,Habit,Count\n"
    all_habits = db.get_all_habits()

    if not all_habits:
        bot.send_message(user_id, "No habits logged yet in the database.")
        return

    for user_id, name, date, habit_name, count in all_habits:
        csv_content += f"{user_id},{name},{date},{habit_name},{count}\n"

    # Create temporary file
    filename = "all_ramadan_logs.csv"
    with open(filename, 'w') as f:
        f.write(csv_content)

    # Send the file
    with open(filename, 'rb') as f:
        bot.send_document(user_id, f, caption="Here are all Ramadan habit logs in CSV format.")

    # Clean up temporary file
    import os
    os.remove(filename)

    bot.send_message(user_id, "This CSV file contains all user logs. Open it in Google Sheets for analysis.")

@bot.message_handler(commands=['synctosheets'])
def sync_to_sheets(message):
    user_id = message.chat.id

    # Admin check - replace this with your actual Telegram user ID
    admin_id = 5861883539  # Your Telegram ID
    if user_id != admin_id:
        bot.send_message(user_id, "Sorry, this command is restricted to admin use only.")
        return

    if not db.sheets.is_ready():
        bot.send_message(user_id, "Google Sheets integration is not configured. Add GOOGLE_CREDENTIALS and GOOGLE_SHEET_ID to your secrets.")
        return

@bot.message_handler(commands=['help'])
def help_command(message):
    user_id = message.chat.id

    # Admin ID check
    admin_id = 5861883539  # Your Telegram ID

    # Get current date in Gregorian and Hijri calendars
    import datetime
    from hijri_converter import Gregorian

    today = datetime.datetime.now()
    gregorian_date = today.strftime("%d %B %Y")

    # Convert to Hijri
    hijri_date = Gregorian(today.year, today.month, today.day).to_hijri()
    hijri_formatted = f"{hijri_date.day} {hijri_date.month_name()} {hijri_date.year}H"

    date_info = f"📅 Today is {gregorian_date}\n📅 {hijri_formatted}"

    # List of available commands - show different commands based on user role
    if user_id == admin_id:
        # Admin commands
        commands = (
            "Available commands (Admin):\n"
            "/start - Start or restart the bot\n"
            "/log - Log your daily Ramadan habits\n"
            "/progress - View your progress\n"
            "/history - View past day logs\n"
            "/leaderboard - See the top performers\n"
            "/export - Export your data as CSV\n"
            "/users - View all users data\n"
            "/database - Database statistics\n"
            "/exportall - Export all users' data\n"
            "/synctosheets - Sync data to Google Sheets\n"
            "/debugsheets - Check Google Sheets integration\n"
            "/setupsheets - Get help setting up Google Sheets\n"
            "/resetdatabase - ⚠️ Reset all database data"
        )
    else:
        # Regular user commands
        commands = (
            "Available commands:\n"
            "/start - Start or restart the bot\n"
            "/log - Log your daily Ramadan habits\n"
            "/progress - View your progress\n"
            "/history - View past day logs\n"
            "/leaderboard - See top performers\n"
            "/export - Export your data as CSV"
        )

    bot.send_message(user_id, f"{date_info}\n\n{commands}")

def confirm_database_reset(message):
    user_id = message.chat.id

    # Admin check
    admin_id = 5861883539  # Your Telegram ID
    if user_id != admin_id:
        bot.send_message(user_id, "Sorry, this command is restricted to admin use only.")
        return

    response = message.text.strip().upper()

    if response == "YES, RESET DATABASE":
        # Call database reset function
        success = db.reset_database()

        if success:
            bot.send_message(
                user_id, 
                "✅ Database has been completely reset.\n"
                "All user data and habit logs have been removed.\n"
                "The bot is ready for fresh data."
            )
        else:
            bot.send_message(
                user_id,
                "❌ An error occurred while trying to reset the database.\n"
                "Please check the logs for more information."
            )
    else:
        bot.send_message(user_id, "Database reset cancelled. Your data is safe.")


    # Get all habits
    all_habits = db.get_all_habits(days=365)  # Get all data from the past year

    if not all_habits:
        bot.send_message(user_id, "No habits logged yet in the database.")
        return

    # Upload to Google Sheets
    success = db.sheets.bulk_upload(all_habits)

    if success:
        bot.send_message(user_id, "✅ All data has been synced to Google Sheets successfully!")
    else:
        bot.send_message(user_id, "❌ Failed to sync data to Google Sheets. Check console for errors.")

@bot.message_handler(commands=['debugsheets'])
def debug_sheets(message):
    user_id = message.chat.id

    # Admin check - replace this with your actual Telegram user ID
    admin_id = 5861883539  # Your Telegram ID
    if user_id != admin_id:
        bot.send_message(user_id, "Sorry, this command is restricted to admin use only.")
        return

    debug_info = "Google Sheets Debug Info:\n"

    # Check if the sheets manager is initialized
    if not db.sheets.is_ready():
        debug_info += "❌ Sheets integration is not properly configured\n"
    else:
        debug_info += "✅ Sheets integration is properly configured\n"

    # Check if credentials are available
    import os
    if 'GOOGLE_CREDENTIALS' in os.environ:
        cred_preview = os.environ.get('GOOGLE_CREDENTIALS')[:20] + "..." if os.environ.get('GOOGLE_CREDENTIALS') else "None"
        debug_info += f"✅ GOOGLE_CREDENTIALS found (preview: {cred_preview})\n"
    else:
        debug_info += "❌ GOOGLE_CREDENTIALS not found\n"

    # Check if sheet ID is available
    if 'GOOGLE_SHEET_ID' in os.environ and os.environ.get('GOOGLE_SHEET_ID'):
        sheet_id = os.environ.get('GOOGLE_SHEET_ID')
        debug_info += f"✅ GOOGLE_SHEET_ID found: {sheet_id[:5]}...\n"
    else:
        debug_info += "❌ GOOGLE_SHEET_ID not found\n"

    bot.send_message(user_id, debug_info)


@bot.message_handler(commands=['setupsheets'])
def setup_sheets(message):
    user_id = message.chat.id

    # Admin check - replace this with your actual Telegram user ID
    admin_id = 5861883539  # Your Telegram ID
    if user_id != admin_id:
        bot.send_message(user_id, "Sorry, this command is restricted to admin use only.")
        return

    instructions = (
        "To set up Google Sheets integration, follow these steps:\n\n"
        "1. Add your service account credentials as a secret named GOOGLE_CREDENTIALS\n"
        "2. Add your Google Sheet ID as a secret named GOOGLE_SHEET_ID\n"
        "3. Share your Google Sheet with the service account email: ramadan-tracker@quantum-transit-452222-v1.iam.gserviceaccount.com\n\n"
        "You can use /debugsheets to check if your credentials are properly configured."
    )

    bot.send_message(user_id, instructions)

@bot.message_handler(commands=['resetdatabase'])
def reset_database(message):
    user_id = message.chat.id

    # Admin check
    admin_id = 5861883539  # Your Telegram ID
    if user_id != admin_id:
        bot.send_message(user_id, "Sorry, this command is restricted to admin use only.")
        return

    # Confirmation step
    markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(KeyboardButton("YES, RESET DATABASE"), KeyboardButton("CANCEL"))
    msg = bot.send_message(
        user_id, 
        "⚠️ WARNING ⚠️\n\nThis will DELETE ALL USER DATA and HABITS from the database.\n"
        "This action CANNOT be undone!\n\n"
        "Are you absolutely sure you want to reset the database?",
        reply_markup=markup
    )
    bot.register_next_step_handler(msg, confirm_database_reset)