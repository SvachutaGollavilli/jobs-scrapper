import re
import os
import json
from datetime import datetime, timedelta
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class DuplicatesPipeline:
    def __init__(self):
        self.ids_seen = set()
        self.load_existing_ids()
    
    def load_existing_ids(self):
        """Load existing job IDs to avoid re-processing"""
        try:
            if os.path.exists('processed_jobs.json'):
                with open('processed_jobs.json', 'r') as f:
                    data = json.load(f)
                    self.ids_seen = set(data.get('job_ids', []))
        except Exception as e:
            print(f"Error loading existing IDs: {e}")
    
    def save_job_ids(self):
        """Save processed job IDs"""
        try:
            with open('processed_jobs.json', 'w') as f:
                json.dump({'job_ids': list(self.ids_seen)}, f)
        except Exception as e:
            print(f"Error saving job IDs: {e}")
    
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        # Create unique identifier
        job_id = adapter.get('job_id', '')
        company = adapter.get('company', '').lower().replace(' ', '_')
        title = adapter.get('title', '').lower().replace(' ', '_')
        
        if not job_id:
            job_id = f"{company}_{title}"
            job_id = re.sub(r'[^a-z0-9_]', '', job_id)
        
        unique_id = f"{job_id}_{adapter.get('source', '')}"
        
        if unique_id in self.ids_seen:
            raise DropItem(f"Duplicate item found: {unique_id}")
        else:
            self.ids_seen.add(unique_id)
            adapter['unique_id'] = unique_id
            return item
    
    def close_spider(self, spider):
        self.save_job_ids()

class DataCleaningPipeline:
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        # Clean text fields
        text_fields = ['title', 'company', 'location', 'description']
        for field in text_fields:
            value = adapter.get(field)
            if value:
                # Remove extra whitespace and normalize
                cleaned = re.sub(r'\s+', ' ', str(value)).strip()
                # Remove problematic characters
                cleaned = cleaned.replace('\n', ' ').replace('\r', ' ')
                cleaned = cleaned.replace('"', "'")  # Prevent CSV issues
                adapter[field] = cleaned
        
        # Standardize salary
        salary = adapter.get('salary')
        if salary:
            # Extract and format salary numbers
            salary_numbers = re.findall(r'\$[\d,]+', salary)
            if salary_numbers:
                adapter['salary'] = ' - '.join(salary_numbers)
        
        # Set defaults
        adapter.setdefault('application_status', 'Not Applied')
        adapter.setdefault('notes', '')
        adapter.setdefault('keywords', [])
        adapter.setdefault('priority_score', 0)
        adapter.setdefault('auto_apply_eligible', False)
        
        return item

class AutoApplicationPipeline:
    def __init__(self):
        self.applications_today = 0
        self.max_applications = int(os.getenv('MAX_APPLICATIONS_PER_DAY', '10'))
        self.email_address = os.getenv('EMAIL_ADDRESS')
        self.email_password = os.getenv('EMAIL_PASSWORD')
        
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        # Check if auto-apply is enabled and eligible
        if (adapter.get('auto_apply_eligible') and 
            self.applications_today < self.max_applications and
            adapter.get('priority_score', 0) >= 25):
            
            try:
                success = self.attempt_auto_application(adapter, spider)
                if success:
                    adapter['application_status'] = 'Auto Applied'
                    adapter['notes'] = f'Auto-applied on {datetime.now().strftime("%Y-%m-%d")}'
                    self.applications_today += 1
                    spider.logger.info(f"Auto-applied to {adapter.get('company')} - {adapter.get('title')}")
                else:
                    adapter['application_status'] = 'Auto Apply Failed'
                    
            except Exception as e:
                spider.logger.error(f"Auto-application error: {e}")
                adapter['application_status'] = 'Auto Apply Error'
                adapter['notes'] = f'Auto-apply error: {str(e)}'
        
        return item
    
    def attempt_auto_application(self, adapter, spider):
        """Attempt to auto-apply to jobs where legally possible"""
        
        source = adapter.get('source', '').lower()
        application_method = adapter.get('application_method', '').lower()
        
        if source == 'indeed' and 'easy apply' in application_method:
            return self.indeed_auto_apply(adapter, spider)
        elif source == 'linkedin' and 'easy apply' in application_method:
            # LinkedIn auto-apply is very risky - proceed with extreme caution
            spider.logger.warning("LinkedIn auto-apply attempted - HIGH RISK!")
            return self.linkedin_auto_apply(adapter, spider)
        else:
            # For external applications, send email if contact found
            return self.email_auto_apply(adapter, spider)
    
    def indeed_auto_apply(self, adapter, spider):
        """Auto-apply to Indeed Easy Apply jobs"""
        try:
            from selenium import webdriver
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            import undetected_chromedriver as uc
            
            # Use undetected chrome for better success rate
            options = uc.ChromeOptions()
            options.add_argument('--headless=new')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            
            driver = uc.Chrome(options=options)
            
            try:
                # Navigate to job page
                driver.get(adapter.get('job_url'))
                
                # Wait for and click "Apply Now" button
                apply_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='indeedApplyButton']"))
                )
                
                # Human-like delay
                import time
                time.sleep(2 + (time.time() % 3))
                
                apply_button.click()
                
                # Wait for application form
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "form"))
                )
                
                # Fill out basic information (if form appears)
                self.fill_indeed_application_form(driver, adapter)
                
                # Submit application
                submit_button = driver.find_element(By.CSS_SELECTOR, "[data-testid='submit-application']")
                submit_button.click()
                
                # Wait for confirmation
                time.sleep(5)
                
                # Check for success confirmation
                success_indicators = [
                    "application submitted",
                    "application sent",
                    "thank you",
                    "applied successfully"
                ]
                
                page_text = driver.page_source.lower()
                success = any(indicator in page_text for indicator in success_indicators)
                
                return success
                
            finally:
                driver.quit()
                
        except Exception as e:
            spider.logger.error(f"Indeed auto-apply failed: {e}")
            return False
    
    def fill_indeed_application_form(self, driver, adapter):
        """Fill out Indeed application form"""
        try:
            # Fill common form fields
            form_fields = {
                'firstName': 'Your',
                'lastName': 'Name',
                'email': self.email_address,
                'phoneNumber': '(555) 123-4567',
                'location': 'Your City, State'
            }
            
            for field_name, value in form_fields.items():
                try:
                    field = driver.find_element(By.NAME, field_name)
                    field.clear()
                    field.send_keys(value)
                except:
                    # Try by ID if name doesn't work
                    try:
                        field = driver.find_element(By.ID, field_name)
                        field.clear()
                        field.send_keys(value)
                    except:
                        continue
            
            # Handle resume upload (if required)
            try:
                upload_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
                if upload_input and os.path.exists('resume.pdf'):
                    upload_input.send_keys(os.path.abspath('resume.pdf'))
            except:
                pass
            
        except Exception as e:
            print(f"Form filling error: {e}")
    
    def linkedin_auto_apply(self, adapter, spider):
        """LinkedIn auto-apply (VERY HIGH RISK - USE WITH EXTREME CAUTION)"""
        spider.logger.warning("LinkedIn auto-apply is EXTREMELY RISKY and likely to result in account suspension!")
        
        # For safety, we'll skip LinkedIn auto-apply by default
        # Uncomment and modify at your own risk
        return False
        
        # RISKY CODE (commented out for safety):
        """
        try:
            from selenium import webdriver
            # ... LinkedIn auto-apply logic would go here
            # This is intentionally left incomplete due to high risk
            return False
        except Exception as e:
            spider.logger.error(f"LinkedIn auto-apply failed: {e}")
            return False
        """
    
    def email_auto_apply(self, adapter, spider):
        """Send email application for external jobs"""
        if not self.email_address or not self.email_password:
            return False
        
        try:
            # Look for contact email in job description
            description = adapter.get('description', '')
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, description)
            
            if not emails:
                return False
            
            contact_email = emails[0]  # Use first found email
            
            # Create email content
            subject = f"Application for {adapter.get('title')} position"
            
            body = f"""
Dear Hiring Manager,

I am writing to express my interest in the {adapter.get('title')} position at {adapter.get('company')}.

My background includes experience with {', '.join(adapter.get('keywords', [])[:5])} which aligns with your requirements.

I have attached my resume for your review and would welcome the opportunity to discuss how my skills can contribute to your team.

Best regards,
[Your Name]
[Your Phone]
{self.email_address}

---
Job Reference: {adapter.get('job_url')}
"""
            
            # Send email
            success = self.send_email(contact_email, subject, body)
            
            if success:
                adapter['contact_email'] = contact_email
                adapter['email_sent'] = True
            
            return success
            
        except Exception as e:
            spider.logger.error(f"Email auto-apply failed: {e}")
            return False
    
    def send_email(self, to_email, subject, body):
        """Send application email"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_address
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Attach resume if available
            if os.path.exists('resume.pdf'):
                from email.mime.base import MIMEBase
                from email import encoders
                
                with open('resume.pdf', 'rb') as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    'attachment; filename= resume.pdf'
                )
                msg.attach(part)
            
            # Send email
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(self.email_address, self.email_password)
            server.send_message(msg)
            server.quit()
            
            return True
            
        except Exception as e:
            print(f"Email sending failed: {e}")
            return False

class GoogleSheetsPipeline:
    def __init__(self):
        self.items = []
        self.sheet_id = os.getenv('GOOGLE_SHEETS_JOB_ID')
        self.credentials_path = os.getenv('GOOGLE_CREDENTIALS_PATH', 'google_credentials.json')
        
    def open_spider(self, spider):
        if not self.sheet_id:
            spider.logger.warning("Google Sheets ID not provided")
            return
            
        try:
            scope = ['https://spreadsheets.google.com/feeds',
                    'https://www.googleapis.com/auth/drive']
            
            creds = ServiceAccountCredentials.from_json_keyfile_name(
                self.credentials_path, scope)
            
            self.client = gspread.authorize(creds)
            spider.logger.info("Google Sheets connection established")
        except Exception as e:
            spider.logger.error(f"Failed to connect to Google Sheets: {e}")
            self.client = None
    
    def process_item(self, item, spider):
        self.items.append(ItemAdapter(item).asdict())
        return item
    
    def close_spider(self, spider):
        if not self.items:
            return
        
        # Save to local backup
        self.save_local_backup(spider)
        
        # Save to Google Sheets
        if self.client and self.sheet_id:
            self.save_to_google_sheets(spider)
    
    def save_local_backup(self, spider):
        """Save to local Excel file as backup"""
        try:
            df = pd.DataFrame(self.items)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"jobs_backup_{spider.name}_{timestamp}.xlsx"
            df.to_excel(filename, index=False)
            spider.logger.info(f"Saved {len(self.items)} jobs to {filename}")
        except Exception as e:
            spider.logger.error(f"Failed to save local backup: {e}")
    
    def save_to_google_sheets(self, spider):
        """Save jobs to Google Sheets with proper formatting"""
        try:
            sheet = self.client.open_by_key(self.sheet_id)
            
            # Get or create worksheet
            worksheet_name = "Job Pipeline"
            try:
                worksheet = sheet.worksheet(worksheet_name)
            except gspread.WorksheetNotFound:
                worksheet = sheet.add_worksheet(title=worksheet_name, rows=1000, cols=25)
                
                # Add headers
                headers = [
                    'Date', 'Priority', 'Status', 'Title', 'Company', 'Location',
                    'Salary', 'Source', 'Keywords', 'Experience Level', 'Remote',
                    'Priority Score', 'Job URL', 'Apply URL', 'Easy Apply',
                    'Application Method', 'Auto Apply Eligible', 'Application Status',
                    'Notes', 'Posted Date', 'Scraped Date', 'Follow Up Date',
                    'Applied Date', 'Response Date', 'Next Action'
                ]
                
                worksheet.insert_row(headers, 1)
            
            # Prepare data
            data_rows = []
            for item in self.items:
                row = [
                    datetime.now().strftime("%Y-%m-%d"),  # Date
                    item.get('priority_score', 0),  # Priority
                    item.get('application_status', 'Not Applied'),  # Status
                    item.get('title', ''),  # Title
                    item.get('company', ''),  # Company
                    item.get('location', ''),  # Location
                    item.get('salary', ''),  # Salary
                    item.get('source', ''),  # Source
                    ', '.join(item.get('keywords', [])),  # Keywords
                    item.get('experience_level', ''),  # Experience Level
                    'Yes' if item.get('remote_friendly') else 'No',  # Remote
                    item.get('priority_score', 0),  # Priority Score
                    item.get('job_url', ''),  # Job URL
                    item.get('apply_url', ''),  # Apply URL
                    'Yes' if item.get('easy_apply_available') else 'No',  # Easy Apply
                    item.get('application_method', ''),  # Application Method
                    'Yes' if item.get('auto_apply_eligible') else 'No',  # Auto Apply Eligible
                    item.get('application_status', 'Not Applied'),  # Application Status
                    item.get('notes', ''),  # Notes
                    item.get('posted_date', ''),  # Posted Date
                    item.get('scraped_date', ''),  # Scraped Date
                    '',  # Follow Up Date
                    '',  # Applied Date
                    '',  # Response Date
                    'Review & Apply' if item.get('priority_score', 0) >= 20 else 'Low Priority'  # Next Action
                ]
                data_rows.append(row)
            
            # Append data to sheet
            if data_rows:
                worksheet.append_rows(data_rows)
                spider.logger.info(f"Added {len(data_rows)} jobs to Google Sheets")
            
        except Exception as e:
            spider.logger.error(f"Failed to save to Google Sheets: {e}")

