
import sqlite3
import datetime
import pytz
from sheets import SheetsManager

class Database:
    def __init__(self, db_file="ramadan_tracker.db"):
        self.db_file = db_file
        # Add timeout to avoid database locked errors
        self.conn = sqlite3.connect(db_file, check_same_thread=False, timeout=30)
        self.cursor = self.conn.cursor()
        self.setup_database()
        
        # Initialize Google Sheets integration
        self.sheets = SheetsManager()
        
    def setup_database(self):
        # Create users table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        )
        ''')
        
        # Create habits table to track all habits
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS habits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            habit_name TEXT NOT NULL,
            date TEXT NOT NULL,
            count INTEGER DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users (user_id),
            UNIQUE(user_id, habit_name, date)
        )
        ''')
        
        self.conn.commit()
    
    def add_user(self, user_id, name):
        try:
            self.cursor.execute("INSERT OR REPLACE INTO users (user_id, name) VALUES (?, ?)", 
                               (user_id, name))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error adding user: {e}")
            return False
    
    def get_user_name(self, user_id):
        self.cursor.execute("SELECT name FROM users WHERE user_id = ?", (user_id,))
        result = self.cursor.fetchone()
        return result[0] if result else None
    
    def log_habit(self, user_id, habit_name, count=1):
        # Use Eastern time zone for consistent daily reset
        eastern = pytz.timezone('US/Eastern')
        today = datetime.datetime.now(eastern).strftime("%Y-%m-%d")
        try:
            # Try to update existing record for today
            self.cursor.execute("""
                INSERT INTO habits (user_id, habit_name, date, count) 
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id, habit_name, date) 
                DO UPDATE SET count = count + ?
            """, (user_id, habit_name, today, count, count))
            self.conn.commit()
            
            # Sync to Google Sheets if configured
            if self.sheets.is_ready():
                # Get user name
                name = self.get_user_name(user_id)
                # Upload to sheets
                self.sheets.upload_habit(user_id, name, today, habit_name, count)
                
            return True
        except Exception as e:
            print(f"Error logging habit: {e}")
            return False
    
    def set_prayer_count(self, user_id, count):
        """Specifically for daily prayers (1-5) where we want to set the exact count"""
        # Use Eastern time zone for consistent daily reset
        eastern = pytz.timezone('US/Eastern')
        today = datetime.datetime.now(eastern).strftime("%Y-%m-%d")
        try:
            self.cursor.execute("""
                INSERT INTO habits (user_id, habit_name, date, count) 
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id, habit_name, date) 
                DO UPDATE SET count = ?
            """, (user_id, "prayer", today, count, count))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error setting prayer count: {e}")
            return False
    
    def get_today_habit_count(self, user_id, habit_name):
        # Use Eastern time zone for consistent daily reset
        eastern = pytz.timezone('US/Eastern')
        today = datetime.datetime.now(eastern).strftime("%Y-%m-%d")
        self.cursor.execute("""
            SELECT count FROM habits 
            WHERE user_id = ? AND habit_name = ? AND date = ?
        """, (user_id, habit_name, today))
        result = self.cursor.fetchone()
        return result[0] if result else 0
    
    def get_habit_count(self, user_id, habit_name, days=30):
        """Get total count for a habit over the last N days"""
        eastern = pytz.timezone('US/Eastern')
        cutoff_date = (datetime.datetime.now(eastern) - datetime.timedelta(days=days)).strftime("%Y-%m-%d")
        self.cursor.execute("""
            SELECT SUM(count) FROM habits 
            WHERE user_id = ? AND habit_name = ? AND date >= ?
        """, (user_id, habit_name, cutoff_date))
        result = self.cursor.fetchone()
        return result[0] if result and result[0] else 0
    
    def get_habit_days(self, user_id, habit_name, days=30):
        """Get number of days a habit was logged over the last N days"""
        eastern = pytz.timezone('US/Eastern')
        cutoff_date = (datetime.datetime.now(eastern) - datetime.timedelta(days=days)).strftime("%Y-%m-%d")
        self.cursor.execute("""
            SELECT COUNT(DISTINCT date) FROM habits 
            WHERE user_id = ? AND habit_name = ? AND date >= ?
        """, (user_id, habit_name, cutoff_date))
        result = self.cursor.fetchone()
        return result[0] if result else 0
    
    def get_all_users(self):
        self.cursor.execute("SELECT user_id, name FROM users")
        return self.cursor.fetchall()
    
    def get_leaderboard(self, days=30):
        """Get leaderboard data for all users"""
        eastern = pytz.timezone('US/Eastern')
        cutoff_date = (datetime.datetime.now(eastern) - datetime.timedelta(days=days)).strftime("%Y-%m-%d")
        self.cursor.execute("""
            SELECT u.user_id, u.name, SUM(h.count) as total_points
            FROM users u
            JOIN habits h ON u.user_id = h.user_id
            WHERE h.date >= ?
            GROUP BY u.user_id, u.name
            ORDER BY total_points DESC
        """, (cutoff_date,))
        return self.cursor.fetchall()
        
    def get_habit_leaderboard(self, habit_name, days=30):
        """Get leaderboard data for a specific habit"""
        eastern = pytz.timezone('US/Eastern')
        cutoff_date = (datetime.datetime.now(eastern) - datetime.timedelta(days=days)).strftime("%Y-%m-%d")
        
        if habit_name in ["taraweeh", "tahajjud"]:
            # For taraweeh and tahajjud, count the number of days completed
            self.cursor.execute("""
                SELECT u.user_id, u.name, COUNT(DISTINCT h.date) as days_completed
                FROM users u
                JOIN habits h ON u.user_id = h.user_id
                WHERE h.habit_name = ? AND h.date >= ?
                GROUP BY u.user_id, u.name
                ORDER BY days_completed DESC
            """, (habit_name, cutoff_date))
        else:
            # For other habits, sum the counts
            self.cursor.execute("""
                SELECT u.user_id, u.name, SUM(h.count) as total_count
                FROM users u
                JOIN habits h ON u.user_id = h.user_id
                WHERE h.habit_name = ? AND h.date >= ?
                GROUP BY u.user_id, u.name
                ORDER BY total_count DESC
            """, (habit_name, cutoff_date))
            
        return self.cursor.fetchall()
    
    def close(self):
        self.conn.close()
    
    def reset_database(self):
        """Reset the entire database by dropping all tables and recreating them"""
        try:
            # Drop existing tables
            self.cursor.execute("DROP TABLE IF EXISTS habits")
            self.cursor.execute("DROP TABLE IF EXISTS users")
            self.conn.commit()
            
            # Recreate tables
            self.setup_database()
            
            print("Database has been reset successfully")
            return True
        except Exception as e:
            print(f"Error resetting database: {e}")
            return False
        
    def get_user_habits(self, user_id, days=30):
        """Get all habit logs for a user over the last N days"""
        eastern = pytz.timezone('US/Eastern')
        cutoff_date = (datetime.datetime.now(eastern) - datetime.timedelta(days=days)).strftime("%Y-%m-%d")
        self.cursor.execute("""
            SELECT date, habit_name, count 
            FROM habits 
            WHERE user_id = ? AND date >= ?
            ORDER BY date DESC
        """, (user_id, cutoff_date))
        return self.cursor.fetchall()
        
    def get_user_habits_for_date(self, user_id, date_string):
        """Get all habits for a user on a specific date"""
        self.cursor.execute("""
            SELECT habit_name, count 
            FROM habits 
            WHERE user_id = ? AND date = ?
            ORDER BY habit_name
        """, (user_id, date_string))
        return self.cursor.fetchall()
        
    def get_all_habits(self, days=30):
        """Get all habit logs with user information over the last N days"""
        eastern = pytz.timezone('US/Eastern')
        cutoff_date = (datetime.datetime.now(eastern) - datetime.timedelta(days=days)).strftime("%Y-%m-%d")
        self.cursor.execute("""
            SELECT h.user_id, u.name, h.date, h.habit_name, h.count 
            FROM habits h
            JOIN users u ON h.user_id = u.user_id
            WHERE h.date >= ?
            ORDER BY h.date DESC
        """, (cutoff_date,))
        return self.cursor.fetchall()
