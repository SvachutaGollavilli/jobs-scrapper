import os
import time
import json
import schedule
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc
from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials

load_dotenv()

class JobAutoApplier:
    def __init__(self):
        self.max_applications_per_day = int(os.getenv('MAX_APPLICATIONS_PER_DAY', '10'))
        self.applications_today = 0
        self.email = os.getenv('EMAIL_ADDRESS')
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
            print(f"Google Sheets setup failed: {e}")
            self.client = None
    
    def get_jobs_to_apply(self):
        """Get jobs eligible for auto-application from Google Sheets"""
        if not self.client:
            return []
        
        try:
            sheet = self.client.open_by_key(self.sheet_id)
            worksheet = sheet.worksheet("Job Pipeline")
            
            # Get all records
            records = worksheet.get_all_records()
            
            # Filter for auto-apply eligible jobs
            eligible_jobs = []
            for i, record in enumerate(records, start=2):  # Start at row 2 (after header)
                if (record.get('Auto Apply Eligible') == 'Yes' and
                    record.get('Application Status') == 'Not Applied' and
                    record.get('Priority Score', 0) >= 25):
                    
                    record['row_number'] = i
                    eligible_jobs.append(record)
            
            # Sort by priority score
            eligible_jobs.sort(key=lambda x: x.get('Priority Score', 0), reverse=True)
            
            return eligible_jobs[:self.max_applications_per_day - self.applications_today]
            
        except Exception as e:
            print(f"Error getting jobs from sheets: {e}")
            return []
    
    def apply_to_indeed_job(self, job):
        """Apply to Indeed Easy Apply job"""
        print(f"Attempting to apply to {job['Company']} - {job['Title']}")
        
        options = uc.ChromeOptions()
        # options.add_argument('--headless=new')  # Comment out for debugging
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        
        driver = uc.Chrome(options=options)
        
        try:
            # Navigate to job page
            driver.get(job['Job URL'])
            
            # Wait for page to load
            time.sleep(3)
            
            # Look for "Apply now" button
            apply_selectors = [
                "[data-testid='indeedApplyButton']",
                ".ia-IndeedApplyButton",
                "button[aria-label*='Apply']",
                "a[aria-label*='Apply']"
            ]
            
            apply_button = None
            for selector in apply_selectors:
                try:
                    apply_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    break
                except:
                    continue
            
            if not apply_button:
                print("Apply button not found")
                return False
            
            # Click apply button
            driver.execute_script("arguments[0].scrollIntoView();", apply_button)
            time.sleep(1)
            apply_button.click()
            
            # Wait for application modal/page
            time.sleep(5)
            
            # Fill out application form
            success = self.fill_indeed_application(driver, job)
            
            if success:
                # Submit application
                submit_selectors = [
                    "[data-testid='submit-application']",
                    "button[type='submit']",
                    ".ia-continueButton"
                ]
                
                for selector in submit_selectors:
                    try:
                        submit_button = driver.find_element(By.CSS_SELECTOR, selector)
                        if submit_button.is_enabled():
                            submit_button.click()
                            time.sleep(3)
                            
                            # Check for success
                            if self.check_application_success(driver):
                                print(f"Successfully applied to {job['Company']}")
                                return True
                            break
                    except:
                        continue
            
            return False
            
        except Exception as e:
            print(f"Error applying to job: {e}")
            return False
        finally:
            driver.quit()
    
    def fill_indeed_application(self, driver, job):
        """Fill Indeed application form"""
        try:
            # Common form fields and their values
            form_data = {
                'firstName': 'Your',
                'lastName': 'Name', 
                'email': self.email,
                'phone': '(555) 123-4567',
                'location': 'Your City, State'
            }
            
            # Fill text inputs
            for field_name, value in form_data.items():
                selectors = [f"input[name='{field_name}']", f"input[id='{field_name}']"]
                
                for selector in selectors:
                    try:
                        field = driver.find_element(By.CSS_SELECTOR, selector)
                        field.clear()
                        field.send_keys(value)
                        break
                    except:
                        continue
            
            # Handle resume upload
            try:
                file_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
                if os.path.exists('resume.pdf'):
                    file_input.send_keys(os.path.abspath('resume.pdf'))
            except:
                pass
            
            # Handle cover letter
            try:
                cover_letter_field = driver.find_element(By.CSS_SELECTOR, "textarea[name*='cover']")
                cover_letter_text = f"""Dear Hiring Manager,

I am excited to apply for the {job['Title']} position at {job['Company']}. My experience with {job.get('Keywords', '')[:100]} makes me a strong candidate for this role.

I look forward to discussing how I can contribute to your team.

Best regards,
[Your Name]"""
                cover_letter_field.send_keys(cover_letter_text)
            except:
                pass
            
            # Handle screening questions (basic responses)
            try:
                # Look for yes/no questions
                radio_buttons = driver.find_elements(By.CSS_SELECTOR, "input[type='radio']")
                for radio in radio_buttons:
                    label_text = ""
                    try:
                        # Get associated label text
                        label_id = radio.get_attribute('id')
                        if label_id:
                            label = driver.find_element(By.CSS_SELECTOR, f"label[for='{label_id}']")
                            label_text = label.text.lower()
                    except:
                        pass
                    
                    # Answer common questions
                    if any(word in label_text for word in ['authorized', 'eligible', 'legal']):
                        if 'yes' in label_text:
                            radio.click()
                    elif any(word in label_text for word in ['experience', 'years']):
                        if any(num in label_text for num in ['3', '4', '5']):
                            radio.click()
                
                # Handle dropdown menus
                dropdowns = driver.find_elements(By.CSS_SELECTOR, "select")
                for dropdown in dropdowns:
                    try:
                        from selenium.webdriver.support.ui import Select
                        select = Select(dropdown)
                        
                        # Get the first non-empty option
                        options = select.options
                        if len(options) > 1:
                            select.select_by_index(1)  # Select second option (first is usually blank)
                    except:
                        continue
                        
            except Exception as e:
                print(f"Error handling screening questions: {e}")
            
            time.sleep(2)  # Let form settle
            return True
            
        except Exception as e:
            print(f"Error filling application form: {e}")
            return False
    
    def check_application_success(self, driver):
        """Check if application was submitted successfully"""
        success_indicators = [
            "application submitted",
            "application sent", 
            "thank you for applying",
            "application received",
            "successfully applied"
        ]
        
        try:
            # Wait a moment for success message
            time.sleep(3)
            
            page_text = driver.page_source.lower()
            return any(indicator in page_text for indicator in success_indicators)
            
        except Exception as e:
            print(f"Error checking application success: {e}")
            return False
    
    def update_application_status(self, job, status, notes=""):
        """Update job application status in Google Sheets"""
        if not self.client:
            return
        
        try:
            sheet = self.client.open_by_key(self.sheet_id)
            worksheet = sheet.worksheet("Job Pipeline")
            
            row = job['row_number']
            
            # Update status and notes
            worksheet.update(f'R{row}', status)  # Application Status column
            worksheet.update(f'S{row}', notes)  # Notes column
            worksheet.update(f'W{row}', datetime.now().strftime("%Y-%m-%d"))  # Applied Date column
            
            if status == 'Auto Applied':
                worksheet.update(f'Y{row}', 'Follow up in 1 week')  # Next Action
                
        except Exception as e:
            print(f"Error updating application status: {e}")
    
    def run_auto_applications(self):
        """Run auto-application process"""
        print(f"Starting auto-application process...")
        print(f"Current applications today: {self.applications_today}/{self.max_applications_per_day}")
        
        if self.applications_today >= self.max_applications_per_day:
            print("Daily application limit reached")
            return
        
        # Get jobs to apply to
        jobs = self.get_jobs_to_apply()
        print(f"Found {len(jobs)} jobs eligible for auto-application")
        
        for job in jobs:
            if self.applications_today >= self.max_applications_per_day:
                break
            
            try:
                print(f"\n--- Processing Job {self.applications_today + 1}/{self.max_applications_per_day} ---")
                print(f"Company: {job['Company']}")
                print(f"Title: {job['Title']}")
                print(f"Priority Score: {job['Priority Score']}")
                
                # Only apply to Indeed Easy Apply jobs for safety
                if job.get('Source') == 'Indeed' and job.get('Easy Apply') == 'Yes':
                    success = self.apply_to_indeed_job(job)
                    
                    if success:
                        self.applications_today += 1
                        self.update_application_status(job, 'Auto Applied', 
                                                     f'Auto-applied on {datetime.now().strftime("%Y-%m-%d")}')
                        print(f"✅ Successfully applied!")
                        
                        # Add delay between applications
                        time.sleep(30)  # 30 second delay
                        
                    else:
                        self.update_application_status(job, 'Auto Apply Failed',
                                                     'Auto-application unsuccessful')
                        print(f"❌ Application failed")
                        
                else:
                    print(f"⏭️  Skipping (not Indeed Easy Apply)")
                    
            except Exception as e:
                print(f"❌ Error processing job: {e}")
                self.update_application_status(job, 'Auto Apply Error', str(e))
        
        print(f"\nAuto-application session complete. Applied to {self.applications_today} jobs today.")

def run_daily_auto_apply():
    """Daily auto-application job"""
    applier = JobAutoApplier()
    applier.run_auto_applications()

if __name__ == "__main__":
    # Schedule daily auto-applications
    schedule.every().day.at("09:00").do(run_daily_auto_apply)
    schedule.every().day.at("15:00").do(run_daily_auto_apply)  # Twice daily
    
    print("Auto-applier service started. Scheduled for 9 AM and 3 PM daily.")
    print("Press Ctrl+C to stop.")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        print("\nAuto-applier service stopped.")
