import os
import subprocess
import schedule
import time
from datetime import datetime
import json
from dotenv import load_dotenv

load_dotenv()

class JobScrapingOrchestrator:
    def __init__(self):
        self.scraped_today = 0
        self.max_daily_scraping = 3  # Max scraping sessions per day
        
    def run_indeed_scraper(self):
        """Run Indeed spider"""
        print(f"🕷️  Starting Indeed scraper at {datetime.now()}")
        
        try:
            result = subprocess.run([
                'scrapy', 'crawl', 'indeed_jobs',
                '-s', 'DOWNLOAD_DELAY=3',
                '-s', 'CONCURRENT_REQUESTS=2'
            ], cwd='scrapy_project', capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Indeed scraping completed successfully")
                return True
            else:
                print(f"❌ Indeed scraping failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Indeed scraper error: {e}")
            return False
    
    def run_linkedin_scraper(self):
        """Run LinkedIn spider (HIGH RISK - disabled by default)"""
        linkedin_enabled = os.getenv('ENABLE_LINKEDIN_SCRAPING', 'false').lower() == 'true'
        
        if not linkedin_enabled:
            print("⚠️  LinkedIn scraping disabled (set ENABLE_LINKEDIN_SCRAPING=true to enable)")
            print("⚠️  WARNING: LinkedIn scraping has very high risk of account suspension!")
            return False
        
        print(f"🕷️  Starting LinkedIn scraper at {datetime.now()}")
        print("⚠️  HIGH RISK: LinkedIn may suspend your account!")
        
        try:
            result = subprocess.run([
                'scrapy', 'crawl', 'linkedin_jobs',
                '-s', 'DOWNLOAD_DELAY=8',
                '-s', 'CONCURRENT_REQUESTS=1'
            ], cwd='scrapy_project', capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ LinkedIn scraping completed")
                return True
            else:
                print(f"❌ LinkedIn scraping failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ LinkedIn scraper error: {e}")
            return False
    
    def run_company_scraper(self):
        """Run company website scraper"""
        print(f"🕷️  Starting company website scraper at {datetime.now()}")
        
        # Add company URLs to scrape
        company_urls = [
            "https://careers.google.com/jobs/results/",
            "https://www.amazon.jobs/en/search.json?base_query=engineer",
            "https://jobs.netflix.com/search?q=engineer",
            "https://careers.microsoft.com/professionals/us/en/search-results"
        ]
        
        # This would need a separate spider implementation
        # For now, return True as placeholder
        print("🏢 Company scraper placeholder - implement company_spider.py")
        return True
    
    def run_daily_scraping(self):
        """Run daily scraping routine"""
        if self.scraped_today >= self.max_daily_scraping:
            print(f"📊 Daily scraping limit reached ({self.scraped_today}/{self.max_daily_scraping})")
            return
        
        print(f"\n🚀 Starting scraping session {self.scraped_today + 1}/{self.max_daily_scraping}")
        print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        results = {
            'session': self.scraped_today + 1,
            'timestamp': datetime.now().isoformat(),
            'scrapers_run': [],
            'success_count': 0,
            'total_jobs': 0
        }
        
        # Run Indeed scraper (safest)
        if self.run_indeed_scraper():
            results['scrapers_run'].append('indeed')
            results['success_count'] += 1
        
        # Run company scraper
        if self.run_company_scraper():
            results['scrapers_run'].append('company')
            results['success_count'] += 1
        
        # Optionally run LinkedIn (very risky)
        linkedin_enabled = os.getenv('ENABLE_LINKEDIN_SCRAPING', 'false').lower() == 'true'
        if linkedin_enabled and self.scraped_today < 1:  # Only once per day max
            if self.run_linkedin_scraper():
                results['scrapers_run'].append('linkedin')
                results['success_count'] += 1
        
        self.scraped_today += 1
        
        # Save session results
        self.save_session_results(results)
        
        print(f"📈 Scraping session complete:")
        print(f"   Scrapers run: {', '.join(results['scrapers_run'])}")
        print(f"   Success rate: {results['success_count']}/{len(results['scrapers_run'])}")
    
    def save_session_results(self, results):
        """Save scraping session results"""
        try:
            # Load existing results
            results_file = 'scraping_results.json'
            if os.path.exists(results_file):
                with open(results_file, 'r') as f:
                    all_results = json.load(f)
            else:
                all_results = {'sessions': []}
            
            all_results['sessions'].append(results)
            
            # Keep only last 30 sessions
            all_results['sessions'] = all_results['sessions'][-30:]
            
            # Save updated results
            with open(results_file, 'w') as f:
                json.dump(all_results, f, indent=2)
                
        except Exception as e:
            print(f"Error saving session results: {e}")
    
    def reset_daily_counters(self):
        """Reset daily counters at midnight"""
        self.scraped_today = 0
        print(f"🔄 Daily counters reset at {datetime.now()}")

def main():
    """Main function to run the job scraping orchestrator"""
    orchestrator = JobScrapingOrchestrator()
    
    # Schedule scraping sessions
    schedule.every().day.at("06:00").do(orchestrator.run_daily_scraping)  # Morning
    schedule.every().day.at("14:00").do(orchestrator.run_daily_scraping)  # Afternoon
    schedule.every().day.at("22:00").do(orchestrator.run_daily_scraping)  # Evening
    
    # Reset counters at midnight
    schedule.every().day.at("00:01").do(orchestrator.reset_daily_counters)
    
    print("🤖 Job Scraping Orchestrator Started")
    print("📅 Scheduled scraping: 6 AM, 2 PM, 10 PM daily")
    print("🔄 Daily reset: 12:01 AM")
    print("⏹️  Press Ctrl+C to stop")
    
    # Run immediate test if requested
    if os.getenv('RUN_IMMEDIATE_TEST', 'false').lower() == 'true':
        print("\n🧪 Running immediate test...")
        orchestrator.run_daily_scraping()
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        print("\n👋 Job Scraping Orchestrator stopped.")

if __name__ == "__main__":
    main()
