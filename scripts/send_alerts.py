import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import requests

load_dotenv()

def send_email_alert(subject, body):
    """Send email alert"""
    email_address = os.getenv('EMAIL_ADDRESS')
    email_password = os.getenv('EMAIL_PASSWORD')
    
    if not email_address or not email_password:
        print("⚠️  Email credentials not configured")
        return False
    
    try:
        msg = MIMEMultipart()
        msg['From'] = email_address
        msg['To'] = email_address  # Send to self
        msg['Subject'] = f"[Job Scraper] {subject}"
        
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(email_address, email_password)
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Email alert sent: {subject}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False

def send_slack_alert(message, webhook_url=None):
    """Send Slack notification"""
    if not webhook_url:
        webhook_url = os.getenv('SLACK_WEBHOOK_URL')
    
    if not webhook_url:
        print("⚠️  Slack webhook not configured")
        return False
    
    try:
        payload = {'text': message}
        response = requests.post(webhook_url, json=payload)
        
        if response.status_code == 200:
            print("✅ Slack alert sent")
            return True
        else:
            print(f"❌ Slack alert failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to send Slack alert: {e}")
        return False

def alert_high_priority_jobs(jobs):
    """Alert when high priority jobs found"""
    if not jobs:
        return
    
    subject = f"🎯 {len(jobs)} High Priority Jobs Found!"
    
    body = f"Found {len(jobs)} high-priority job matches:\n\n"
    
    for job in jobs[:5]:  # Top 5
        body += f"• {job['title']} at {job['company']}\n"
        body += f"  Priority Score: {job['priority_score']}\n"
        body += f"  URL: {job['job_url']}\n\n"
    
    send_email_alert(subject, body)
    
    # Also send to Slack if configured
    slack_msg = f"🎯 *{len(jobs)} High Priority Jobs Found!*\n"
    for job in jobs[:3]:
        slack_msg += f"\n• *{job['title']}* at {job['company']} (Score: {job['priority_score']})"
    
    send_slack_alert(slack_msg)

def alert_application_success(company, title):
    """Alert when application successfully submitted"""
    subject = f"✅ Application Submitted: {company}"
    body = f"Successfully applied to:\n\n{title}\nat {company}"
    
    send_email_alert(subject, body)

def alert_scraping_failure(spider_name, error):
    """Alert when scraping fails"""
    subject = f"❌ Scraping Failed: {spider_name}"
    body = f"Spider {spider_name} failed with error:\n\n{error}"
    
    send_email_alert(subject, body)

def alert_daily_summary(stats):
    """Send daily summary email"""
    subject = "📊 Daily Job Search Summary"
    
    body = f"""
Daily Job Search Summary
{'='*50}

Jobs Scraped:        {stats.get('jobs_scraped', 0)}
Applications Sent:   {stats.get('applications_sent', 0)}
High Priority Jobs:  {stats.get('high_priority', 0)}
Resumes Generated:   {stats.get('resumes_generated', 0)}

{'='*50}

Check your Google Sheets for full details:
{os.getenv('GOOGLE_SHEETS_URL', 'Not configured')}
"""
    
    send_email_alert(subject, body)

if __name__ == "__main__":
    # Test alerts
    print("🧪 Testing alert system...")
    
    test_email = send_email_alert(
        "Test Alert",
        "This is a test alert from the job scraper system."
    )
    
    if test_email:
        print("✅ Email alerts working!")
    
    test_slack = send_slack_alert("🧪 Test alert from job scraper")
    
    if test_slack:
        print("✅ Slack alerts working!")
