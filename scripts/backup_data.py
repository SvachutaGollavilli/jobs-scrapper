#!/usr/bin/env python3
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def backup_google_sheet():
    print("💾 Starting Google Sheets backup...")
    
    try:
        scope = ['https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive']
        
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            'google_credentials.json', scope)
        client = gspread.authorize(creds)
        
        sheet_id = os.getenv('GOOGLE_SHEETS_JOB_ID')
        if not sheet_id:
            print("❌ GOOGLE_SHEETS_JOB_ID not found in .env")
            return
        
        sheet = client.open_by_key(sheet_id)
        worksheet = sheet.get_worksheet(0)
        data = worksheet.get_all_records()
        
        if not data:
            print("⚠️  No data found")
            return
        
        df = pd.DataFrame(data)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        os.makedirs('backups', exist_ok=True)
        filename = f"backups/jobs_backup_{timestamp}.xlsx"
        df.to_excel(filename, index=False)
        
        print(f"✅ Backup saved: {filename}")
        print(f"📊 Backed up {len(data)} jobs")
        
    except Exception as e:
        print(f"❌ Backup failed: {e}")

if __name__ == "__main__":
    backup_google_sheet()
