#!/usr/bin/env python3
import os
import sys
import subprocess
from dotenv import load_dotenv

load_dotenv()

def show_menu():
    print("\n🤖 Job Scraper & Auto-Applier")
    print("=" * 40)
    print("1. Run job scraping (Indeed only)")
    print("2. Run job scraping (All sources)")
    print("3. Start auto-applier service")
    print("4. Start resume tailoring API")
    print("5. Run immediate test scrape")
    print("6. View scraping results")
    print("7. Monitor dashboard")
    print("0. Exit")
    print()

def main():
    while True:
        show_menu()
        choice = input("Select option (0-7): ").strip()
        
        if choice == '0':
            print("👋 Goodbye!")
            break
        elif choice == '1':
            print("🕷️  Running Indeed scraper...")
            subprocess.run(['scrapy', 'crawl', 'indeed_jobs'], cwd='scrapy_project')
        elif choice == '2':
            print("🕷️  Running all scrapers...")
            subprocess.run([sys.executable, 'main_scrapper.py'])
        elif choice == '3':
            print("🤖 Starting auto-applier...")
            subprocess.run([sys.executable, 'auto_applier.py'])
        elif choice == '4':
            print("📄 Starting resume API...")
            subprocess.run([sys.executable, 'resume_tailor_api.py'])
        elif choice == '5':
            print("🧪 Running test...")
            os.environ['RUN_IMMEDIATE_TEST'] = 'true'
            subprocess.run([sys.executable, 'main_scrapper.py'])
        elif choice == '6':
            if os.path.exists('scraping_results.json'):
                import json
                with open('scraping_results.json') as f:
                    data = json.load(f)
                    print(f"Sessions: {len(data.get('sessions', []))}")
            else:
                print("No results found")
        elif choice == '7':
            print("📊 Starting monitor...")
            subprocess.run([sys.executable, 'scripts/monitor.py'])
        
        if choice != '0':
            input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()
