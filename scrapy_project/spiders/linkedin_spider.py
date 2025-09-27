import scrapy
from scrapy_selenium import SeleniumRequest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import re
import os
from datetime import datetime, timedelta
from scrapy_project.items import JobItem

class LinkedInJobsSpider(scrapy.Spider):
    name = 'linkedin_jobs'
    allowed_domains = ['linkedin.com']
    
    custom_settings = {
        'DOWNLOAD_DELAY': 8,  # Much longer delays for LinkedIn
        'CONCURRENT_REQUESTS': 1,  # Very conservative
        'RANDOMIZE_DOWNLOAD_DELAY': True,
    }
    
    def __init__(self):
        self.logged_in = False
        self.login_email = os.getenv('LINKEDIN_EMAIL')
        self.login_password = os.getenv('LINKEDIN_PASSWORD')
        
        # WARNING: LinkedIn scraping is high risk
        self.logger.warning("LinkedIn scraping has HIGH RISK of account suspension!")
    
    def start_requests(self):
        # Start with login page
        yield SeleniumRequest(
            url="https://www.linkedin.com/login",
            callback=self.login,
            wait_time=10
        )
    
    def login(self, response):
        """Attempt to login to LinkedIn (HIGH RISK)"""
        if not self.login_email or not self.login_password:
            self.logger.error("LinkedIn credentials not provided. Skipping LinkedIn scraping.")
            return
        
        driver = response.meta['driver']
        
        try:
            # Fill login form
            email_input = driver.find_element(By.ID, "username")
            password_input = driver.find_element(By.ID, "password")
            
            email_input.send_keys(self.login_email)
            time.sleep(2)
            password_input.send_keys(self.login_password)
            time.sleep(2)
            
            # Submit form
            submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            submit_button.click()
            
            # Wait for redirect or CAPTCHA
            time.sleep(10)
            
            # Check if login successful
            if "feed" in driver.current_url or "challenge" in driver.current_url:
                self.logged_in = True
                self.logger.info("LinkedIn login successful")
                
                # Start job searches
                yield from self.start_job_searches(driver)
                
            else:
                self.logger.error("LinkedIn login failed or requires verification")
                
        except Exception as e:
            self.logger.error(f"LinkedIn login error: {e}")
    
    def start_job_searches(self, driver):
        """Start job searches after successful login"""
        keywords = os.getenv('JOB_KEYWORDS', 'data engineer').split(',')
        
        for keyword in keywords[:2]:  # Limit to 2 keywords for LinkedIn
            search_url = f"https://www.linkedin.com/jobs/search/?keywords={keyword.strip().replace(' ', '%20')}&location=United%20States&f_TPR=r86400"
            
            yield SeleniumRequest(
                url=search_url,
                callback=self.parse_job_list,
                meta={'search_keyword': keyword.strip()},
                wait_time=10
            )
    
    def parse_job_list(self, response):
        """Parse job listing page"""
        driver = response.meta['driver']
        
        try:
            # Wait for jobs to load
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".jobs-search-results__list"))
            )
            
            # Scroll to load more jobs
            self.scroll_page(driver)
            
            # Get job links
            job_elements = driver.find_elements(By.CSS_SELECTOR, ".jobs-search-results__list-item")
            
            self.logger.info(f"Found {len(job_elements)} LinkedIn jobs")
            
            for i, job_element in enumerate(job_elements[:20]):  # Limit to 20 jobs
                try:
                    job_link = job_element.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
                    
                    if job_link and '/jobs/view/' in job_link:
                        yield SeleniumRequest(
                            url=job_link,
                            callback=self.parse_job_detail,
                            meta={'search_keyword': response.meta['search_keyword']},
                            wait_time=8
                        )
                        
                        # Longer delay between LinkedIn requests
                        time.sleep(5 + (i % 3))
                        
                except Exception as e:
                    self.logger.warning(f"Error processing LinkedIn job element: {e}")
                    continue
        
        except TimeoutException:
            self.logger.error("LinkedIn job list loading timeout")
    
    def scroll_page(self, driver):
        """Scroll page to load more jobs"""
        try:
            for i in range(3):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)
                
                # Check for "Show more jobs" button
                try:
                    show_more = driver.find_element(By.CSS_SELECTOR, ".infinite-scroller__show-more-button")
                    if show_more and show_more.is_displayed():
                        driver.execute_script("arguments[0].click();", show_more)
                        time.sleep(5)
                except:
                    pass
        except Exception as e:
            self.logger.warning(f"LinkedIn scroll error: {e}")
    
    def parse_job_detail(self, response):
        """Parse individual job details"""
        driver = response.meta['driver']
        
        try:
            # Wait for job details to load
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".jobs-unified-top-card__job-title"))
            )
            
            item = JobItem()
            
            # Basic information
            item['title'] = self.safe_get_text(driver, ".jobs-unified-top-card__job-title h1")
            item['company'] = self.safe_get_text(driver, ".jobs-unified-top-card__company-name a")
            item['location'] = self.safe_get_text(driver, ".jobs-unified-top-card__bullet")
            
            # Try to expand job description
            try:
                show_more = driver.find_element(By.CSS_SELECTOR, "[data-tracking-control-name='public_jobs_show-more-html-btn']")
                if show_more:
                    driver.execute_script("arguments[0].click();", show_more)
                    time.sleep(3)
            except:
                pass
            
            # Get job description
            description_element = driver.find_element(By.CSS_SELECTOR, ".jobs-description__content")
            item['description'] = description_element.text if description_element else ""
            
            # URLs and metadata
            item['job_url'] = response.url
            item['job_id'] = self.extract_linkedin_job_id(response.url)
            item['source'] = 'LinkedIn'
            item['scraped_date'] = datetime.now().isoformat()
            
            # Check for Easy Apply
            easy_apply = driver.find_elements(By.CSS_SELECTOR, "[data-tracking-control-name='public_jobs_apply']")
            item['easy_apply_available'] = len(easy_apply) > 0
            item['apply_url'] = response.url  # LinkedIn applies are done on the same page
            
            # Analysis
            item['keywords'] = self.extract_keywords(item['description'])
            item['experience_level'] = self.determine_experience_level(item['title'], item['description'])
            item['remote_friendly'] = 'remote' in item['location'].lower() if item['location'] else False
            item['priority_score'] = self.calculate_priority_score(item)
            
            # Auto-application analysis
            item['auto_apply_eligible'] = self.check_linkedin_auto_apply_eligibility(item)
            item['application_complexity'] = 'Simple' if item['easy_apply_available'] else 'Complex'
            item['application_method'] = 'LinkedIn Easy Apply' if item['easy_apply_available'] else 'LinkedIn Manual'
            
            # Initialize status
            item['application_status'] = 'Not Applied'
            item['notes'] = ''
            
            yield item
            
        except Exception as e:
            self.logger.error(f"Error parsing LinkedIn job detail: {e}")
    
    def safe_get_text(self, driver, selector):
        """Safely extract text from element"""
        try:
            element = driver.find_element(By.CSS_SELECTOR, selector)
            return element.text.strip()
        except:
            return ""
    
    def extract_linkedin_job_id(self, url):
        """Extract job ID from LinkedIn URL"""
        match = re.search(r'/jobs/view/(\d+)', url)
        return match.group(1) if match else ""
    
    def extract_keywords(self, text):
        """Extract technical keywords from job description"""
        if not text:
            return []
        
        keywords = [
            'Python', 'SQL', 'Machine Learning', 'AWS', 'Docker', 'Kubernetes',
            'TensorFlow', 'PyTorch', 'Spark', 'Airflow', 'Git', 'Linux'
        ]
        
        found = []
        text_lower = text.lower()
        for keyword in keywords:
            if keyword.lower() in text_lower:
                found.append(keyword)
        
        return found
    
    def determine_experience_level(self, title, description):
        """Determine experience level from title and description"""
        content = f"{title} {description}".lower()
        
        if any(word in content for word in ['senior', 'lead', 'principal', 'staff']):
            return 'Senior'
        elif any(word in content for word in ['junior', 'entry', 'associate', 'new grad']):
            return 'Junior'
        else:
            return 'Mid-Level'
    
    def calculate_priority_score(self, item):
        """Calculate priority score for LinkedIn jobs"""
        score = 0
        
        # Company tier
        company = item.get('company', '').lower()
        tier1 = ['google', 'apple', 'microsoft', 'amazon', 'meta', 'netflix']
        if any(comp in company for comp in tier1):
            score += 30  # Higher score for LinkedIn jobs
        
        # Keywords
        keywords = item.get('keywords', [])
        score += len(keywords) * 4
        
        # Easy Apply bonus
        if item.get('easy_apply_available'):
            score += 10
        
        # Remote bonus
        if item.get('remote_friendly'):
            score += 8
        
        return min(score, 50)
    
    def check_linkedin_auto_apply_eligibility(self, item):
        """Check if eligible for LinkedIn auto-apply"""
        # LinkedIn Easy Apply + high priority
        return (item.get('easy_apply_available', False) and 
                item.get('priority_score', 0) >= 25)
