
import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

class SheetsManager:
    def __init__(self):
        # Check if credentials are available
        if 'GOOGLE_CREDENTIALS' in os.environ:
            # Get credentials from environment variable
            creds_json = os.environ.get('GOOGLE_CREDENTIALS')
            creds_dict = json.loads(creds_json)
            
            # Define the scope
            scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
            
            # Authenticate
            self.credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
            self.client = gspread.authorize(self.credentials)
            self.sheet_id = os.environ.get('GOOGLE_SHEET_ID', '')
            self.initialized = bool(self.sheet_id)
        else:
            self.initialized = False
    
    def upload_habit(self, user_id, name, date, habit_name, count):
        """Upload a single habit entry to Google Sheets"""
        if not self.initialized:
            return False
        
        try:
            # Open the spreadsheet
            sheet = self.client.open_by_key(self.sheet_id).sheet1
            
            # Append the data
            sheet.append_row([user_id, name, date, habit_name, count])
            return True
        except Exception as e:
            print(f"Error uploading to Google Sheets: {e}")
            return False
    
    def bulk_upload(self, data):
        """Upload multiple habit entries at once"""
        if not self.initialized:
            return False
        
        try:
            # Open the spreadsheet
            sheet = self.client.open_by_key(self.sheet_id).sheet1
            
            # Prepare data rows
            rows = [[item[0], item[1], item[2], item[3], item[4]] for item in data]
            
            # Append all rows at once
            sheet.append_rows(rows)
            return True
        except Exception as e:
            print(f"Error bulk uploading to Google Sheets: {e}")
            return False
    
    def is_ready(self):
        """Check if the sheets integration is properly configured"""
        if not self.initialized:
            print("Sheets integration not initialized. GOOGLE_CREDENTIALS or GOOGLE_SHEET_ID missing.")
            if 'GOOGLE_CREDENTIALS' not in os.environ:
                print("GOOGLE_CREDENTIALS environment variable is missing")
            else:
                print("GOOGLE_CREDENTIALS is present")
                
            if 'GOOGLE_SHEET_ID' not in os.environ or not os.environ.get('GOOGLE_SHEET_ID'):
                print("GOOGLE_SHEET_ID environment variable is missing or empty")
            else:
                print(f"GOOGLE_SHEET_ID is present: {os.environ.get('GOOGLE_SHEET_ID')[:5]}...")
                
            # Attempt to parse credentials to check if they're valid JSON
            if 'GOOGLE_CREDENTIALS' in os.environ:
                try:
                    json.loads(os.environ.get('GOOGLE_CREDENTIALS'))
                    print("GOOGLE_CREDENTIALS is valid JSON")
                except json.JSONDecodeError as e:
                    print(f"GOOGLE_CREDENTIALS is not valid JSON: {e}")
        return self.initialized
