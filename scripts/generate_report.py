# Generate weekly/monthly job search reports

import os
import json
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv

load_env()

def generate_weekly_report():
    """Generate weekly job search report"""
    print("📊 Generating weekly report...")
    
    # Date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    report = {
        'period': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
        'jobs_scraped': 0,
        'applications_sent': 0,
        'interviews': 0,
        'top_companies': [],
        'top_keywords': [],
        'avg_salary': 0,
        'response_rate': 0
    }
    
    # Get data from Google Sheets
    try:
        scope = ['https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            'google_credentials.json', scope)
        client = gspread.authorize(creds)
        
        sheet_id = os.getenv('GOOGLE_SHEETS_JOB_ID')
        sheet = client.open_by_key(sheet_id)
        worksheet = sheet.worksheet("Job Pipeline")
        
        records = worksheet.get_all_records()
        df = pd.DataFrame(records)
        
        # Filter by date
        df['Scraped Date'] = pd.to_datetime(df['Scraped Date'])
        weekly_data = df[df['Scraped Date'] >= start_date]
        
        # Calculate stats
        report['jobs_scraped'] = len(weekly_data)
        report['applications_sent'] = len(weekly_data[weekly_data['Application Status'].str.contains('Applied', na=False)])
        report['interviews'] = len(weekly_data[weekly_data['Application Status'].str.contains('Interview', na=False)])
        
        # Top companies
        if not weekly_data.empty:
            top_companies = weekly_data['Company'].value_counts().head(5)
            report['top_companies'] = list(zip(top_companies.index, top_companies.values))
        
        # Response rate
        if report['applications_sent'] > 0:
            report['response_rate'] = (report['interviews'] / report['applications_sent']) * 100
        
    except Exception as e:
        print(f"Error generating report: {e}")
    
    # Create report text
    report_text = f"""
╔══════════════════════════════════════════════════════════╗
║          WEEKLY JOB SEARCH REPORT                        ║
╠══════════════════════════════════════════════════════════╣
║  Period: {report['period']}                              ║
╠══════════════════════════════════════════════════════════╣

📊 SUMMARY STATISTICS
────────────────────────────────────────────────────────────
  Jobs Scraped:           {report['jobs_scraped']}
  Applications Sent:      {report['applications_sent']}
  Interviews Scheduled:   {report['interviews']}
  Response Rate:          {report['response_rate']:.1f}%

🏢 TOP COMPANIES (Jobs Found)
────────────────────────────────────────────────────────────
"""
    
    for i, (company, count) in enumerate(report['top_companies'][:5], 1):
        report_text += f"  {i}. {company}: {count} jobs\n"
    
    report_text += f"""
💡 RECOMMENDATIONS
────────────────────────────────────────────────────────────
"""
    
    # Add recommendations
    if report['applications_sent'] < 5:
        report_text += "  ⚠️  Low application count - consider applying to more jobs\n"
    
    if report['response_rate'] < 5:
        report_text += "  ⚠️  Low response rate - review resume and cover letters\n"
    elif report['response_rate'] > 10:
        report_text += "  ✅ Good response rate - keep up the quality applications!\n"
    
    if report['jobs_scraped'] < 50:
        report_text += "  ⚠️  Low job discovery - consider adding more keywords/locations\n"
    
    report_text += """
╚══════════════════════════════════════════════════════════╝
"""
    
    # Save report
    reports_dir = 'reports'
    os.makedirs(reports_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d")
    filename = f"{reports_dir}/weekly_report_{timestamp}.txt"
    
    with open(filename, 'w') as f:
        f.write(report_text)
    
    print(report_text)
    print(f"\n✅ Report saved to: {filename}")
    
    return report

def generate_monthly_report():
    """Generate monthly report"""
    # Similar to weekly but for 30 days
    pass

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate job search reports')
    parser.add_argument('--weekly', action='store_true', help='Generate weekly report')
    parser.add_argument('--monthly', action='store_true', help='Generate monthly report')
    
    args = parser.parse_args()
    
    if args.monthly:
        generate_monthly_report()
    else:
        generate_weekly_report()
