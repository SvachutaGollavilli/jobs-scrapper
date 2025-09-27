import os
import json
from datetime import datetime, timedelta
from pathlib import Path
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv

load_dotenv()

class JobScraperMonitor:
    def __init__(self):
        self.setup_google_sheets()
    
    def setup_google_sheets(self):
        """Setup Google Sheets connection"""
        try:
            scope = ['https://spreadsheets.google.com/feeds',
                    'https://www.googleapis.com/auth/drive']
            creds = ServiceAccountCredentials.from_json_keyfile_name(
                'google_credentials.json', scope)
            self.client = gspread.authorize(creds)
            self.sheet_id = os.getenv('GOOGLE_SHEETS_JOB_ID')
        except Exception as e:
            print(f"⚠️  Could not connect to Google Sheets: {e}")
            self.client = None
    
    def get_scraping_stats(self):
        """Get scraping statistics from results file"""
        stats = {
            'total_sessions': 0,
            'total_jobs': 0,
            'success_rate': 0,
            'last_run': 'Never',
            'sources_used': []
        }
        
        if os.path.exists('scraping_results.json'):
            try:
                with open('scraping_results.json', 'r') as f:
                    data = json.load(f)
                    sessions = data.get('sessions', [])
                    
                    stats['total_sessions'] = len(sessions)
                    
                    if sessions:
                        latest = sessions[-1]
                        stats['last_run'] = latest.get('timestamp', 'Unknown')
                        stats['sources_used'] = latest.get('scrapers_run', [])
                        
                        # Calculate totals
                        total_jobs = sum(s.get('total_jobs', 0) for s in sessions)
                        stats['total_jobs'] = total_jobs
                        
                        # Calculate success rate
                        successful = sum(1 for s in sessions if s.get('success_count', 0) > 0)
                        if sessions:
                            stats['success_rate'] = (successful / len(sessions)) * 100
            except Exception as e:
                print(f"Error reading scraping results: {e}")
        
        return stats
    
    def get_application_stats(self):
        """Get application statistics from Google Sheets"""
        stats = {
            'total_applications': 0,
            'auto_applied': 0,
            'manual_applied': 0,
            'pending': 0,
            'response_rate': 0,
            'interview_count': 0
        }
        
        if not self.client or not self.sheet_id:
            return stats
        
        try:
            sheet = self.client.open_by_key(self.sheet_id)
            worksheet = sheet.worksheet("Job Pipeline")
            records = worksheet.get_all_records()
            
            for record in records:
                status = record.get('Application Status', '')
                
                if 'Applied' in status:
                    stats['total_applications'] += 1
                    
                    if 'Auto' in status:
                        stats['auto_applied'] += 1
                    else:
                        stats['manual_applied'] += 1
                
                if status == 'Not Applied':
                    stats['pending'] += 1
                
                if 'Response' in status or 'Interview' in status:
                    stats['interview_count'] += 1
            
            # Calculate response rate
            if stats['total_applications'] > 0:
                stats['response_rate'] = (stats['interview_count'] / stats['total_applications']) * 100
                
        except Exception as e:
            print(f"Error reading application stats: {e}")
        
        return stats
    
    def get_recent_activity(self, days=7):
        """Get activity from last N days"""
        activity = {
            'jobs_scraped': 0,
            'applications_sent': 0,
            'resumes_generated': 0
        }
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Count recent resumes
        if os.path.exists('tailored_resumes'):
            for file in Path('tailored_resumes').glob('*.docx'):
                file_time = datetime.fromtimestamp(file.stat().st_mtime)
                if file_time > cutoff_date:
                    activity['resumes_generated'] += 1
        
        # Count from scraping results
        if os.path.exists('scraping_results.json'):
            try:
                with open('scraping_results.json', 'r') as f:
                    data = json.load(f)
                    for session in data.get('sessions', []):
                        session_time = datetime.fromisoformat(session['timestamp'])
                        if session_time > cutoff_date:
                            activity['jobs_scraped'] += session.get('total_jobs', 0)
            except:
                pass
        
        return activity
    
    def check_health(self):
        """Check system health"""
        health = {
            'google_sheets': 'Unknown',
            'proxies': 'Unknown',
            'disk_space': 'Unknown',
            'scrapers': 'Unknown'
        }
        
        # Check Google Sheets connection
        health['google_sheets'] = '✅ Connected' if self.client else '❌ Not Connected'
        
        # Check proxies
        if os.path.exists('proxy_list.txt'):
            with open('proxy_list.txt', 'r') as f:
                proxy_count = len([l for l in f.readlines() if ':' in l])
            health['proxies'] = f'✅ {proxy_count} proxies available'
        else:
            health['proxies'] = '❌ No proxy list found'
        
        # Check disk space
        try:
            import shutil
            total, used, free = shutil.disk_usage('.')
            free_gb = free // (2**30)
            if free_gb < 1:
                health['disk_space'] = f'⚠️  Low space: {free_gb}GB free'
            else:
                health['disk_space'] = f'✅ {free_gb}GB free'
        except:
            health['disk_space'] = '❌ Could not check'
        
        # Check scrapers
        if os.path.exists('scrapy_project/spiders'):
            spider_count = len(list(Path('scrapy_project/spiders').glob('*_spider.py')))
            health['scrapers'] = f'✅ {spider_count} scrapers available'
        else:
            health['scrapers'] = '❌ No scrapers found'
        
        return health
    
    def display_dashboard(self):
        """Display monitoring dashboard"""
        print("\n" + "="*60)
        print("📊 JOB SCRAPER MONITORING DASHBOARD")
        print("="*60 + "\n")
        
        # Scraping Stats
        print("🕷️  SCRAPING STATISTICS")
        print("-" * 60)
        scraping = self.get_scraping_stats()
        print(f"  Total Sessions:     {scraping['total_sessions']}")
        print(f"  Total Jobs Found:   {scraping['total_jobs']}")
        print(f"  Success Rate:       {scraping['success_rate']:.1f}%")
        print(f"  Last Run:           {scraping['last_run']}")
        print(f"  Sources Used:       {', '.join(scraping['sources_used']) or 'None'}")
        
        # Application Stats
        print("\n📝 APPLICATION STATISTICS")
        print("-" * 60)
        apps = self.get_application_stats()
        print(f"  Total Applications: {apps['total_applications']}")
        print(f"  Auto-Applied:       {apps['auto_applied']}")
        print(f"  Manual Applied:     {apps['manual_applied']}")
        print(f"  Pending:            {apps['pending']}")
        print(f"  Interviews:         {apps['interview_count']}")
        print(f"  Response Rate:      {apps['response_rate']:.1f}%")
        
        # Recent Activity
        print("\n📈 LAST 7 DAYS ACTIVITY")
        print("-" * 60)
        activity = self.get_recent_activity(7)
        print(f"  Jobs Scraped:       {activity['jobs_scraped']}")
        print(f"  Applications Sent:  {activity['applications_sent']}")
        print(f"  Resumes Generated:  {activity['resumes_generated']}")
        
        # System Health
        print("\n🏥 SYSTEM HEALTH")
        print("-" * 60)
        health = self.check_health()
        print(f"  Google Sheets:      {health['google_sheets']}")
        print(f"  Proxies:            {health['proxies']}")
        print(f"  Disk Space:         {health['disk_space']}")
        print(f"  Scrapers:           {health['scrapers']}")
        
        print("\n" + "="*60 + "\n")

def main():
    """Main monitoring function"""
    monitor = JobScraperMonitor()
    monitor.display_dashboard()

if __name__ == "__main__":
    main()
