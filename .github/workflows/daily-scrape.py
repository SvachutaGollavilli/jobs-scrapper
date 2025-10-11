"""
# GitHub Actions workflow for automated scraping

name: Daily Job Scraping

on:
  schedule:
    # Run at 6 AM, 2 PM, and 10 PM UTC
    - cron: '0 6,14,22 * * *'
  workflow_dispatch:  # Manual trigger

jobs:
  scrape-jobs:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Setup Chrome
      uses: browser-actions/setup-chrome@latest
    
    - name: Create credentials file
      run: |
        echo '${{ secrets.GOOGLE_CREDENTIALS }}' > google_credentials.json
    
    - name: Create .env file
      run: |
        echo "GOOGLE_SHEETS_JOB_ID=${{ secrets.GOOGLE_SHEETS_JOB_ID }}" >> .env
        echo "EMAIL_ADDRESS=${{ secrets.EMAIL_ADDRESS }}" >> .env
        echo "EMAIL_PASSWORD=${{ secrets.EMAIL_PASSWORD }}" >> .env
    
    - name: Run Indeed scraper
      run: |
        cd scrapy_project
        scrapy crawl indeed_jobs
    
    - name: Upload results
      uses: actions/upload-artifact@v4
      with:
        name: job-results
        path: data/jobs_backup_*.xlsx
        retention-days: 30


  """
