import scrapy
from scrapy import Request
from scrapy_project.items import JobItem
from datetime import datetime, timedelta
import re
import urllib.parse
import os

class IndeedJobsSpider(scrapy.Spider):
    name = 'indeed_jobs'
    allowed_domains = ['indeed.com']
    
    custom_settings = {
        'DOWNLOAD_DELAY': 2,
        'CONCURRENT_REQUESTS': 3,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
    }
    
    def start_requests(self):
        # Get search parameters from environment
        keywords = os.getenv('JOB_KEYWORDS', 'data engineer,machine learning engineer').split(',')
        locations = os.getenv('PREFERRED_LOCATIONS', 'Remote,New York,San Francisco').split(',')
        
        base_url = "https://www.indeed.com/jobs"
        
        for keyword in keywords:
            for location in locations:
                params = {
                    'q': keyword.strip(),
                    'l': location.strip(),
                    'sort': 'date',
                    'limit': 50,
                    'fromage': 7  # Last 7 days
                }
                
                url = f"{base_url}?{urllib.parse.urlencode(params)}"
                
                yield Request(
                    url=url,
                    callback=self.parse_job_list,
                    meta={
                        'search_keyword': keyword.strip(),
                        'search_location': location.strip()
                    },
                    headers=self.get_headers()
                )
    
    def parse_job_list(self, response):
        job_cards = response.css('div[data-testid="job-result"]')
        self.logger.info(f"Found {len(job_cards)} jobs on page")
        
        for job_card in job_cards:
            job_link = job_card.css('h2 a::attr(href)').get()
            
            if job_link:
                full_url = response.urljoin(job_link)
                
                yield Request(
                    url=full_url,
                    callback=self.parse_job_detail,
                    meta={
                        'search_keyword': response.meta['search_keyword'],
                        'search_location': response.meta['search_location']
                    },
                    headers=self.get_headers()
                )
        
        # Follow pagination (limit to first 3 pages)
        current_page = response.meta.get('page', 1)
        if current_page < 3:
            next_page = response.css('a[aria-label="Next Page"]::attr(href)').get()
            if next_page:
                yield Request(
                    url=response.urljoin(next_page),
                    callback=self.parse_job_list,
                    meta={
                        **response.meta,
                        'page': current_page + 1
                    },
                    headers=self.get_headers()
                )
    
    def parse_job_detail(self, response):
        item = JobItem()
        
        # Basic information
        item['title'] = response.css('h1 span[title]::attr(title)').get() or ""
        item['company'] = response.css('div[data-testid="inlineHeader-companyName"] a::text').get() or \
                         response.css('div[data-testid="inlineHeader-companyName"] span::text').get() or ""
        item['location'] = response.css('div[data-testid="inlineHeader-companyLocation"] div::text').get() or ""
        
        # Salary information
        salary_elements = response.css('span[data-testid="attribute_snippet_testid"]::text').getall()
        item['salary'] = ' '.join(salary_elements).strip() if salary_elements else ""
        
        # Job description
        description_element = response.css('div[data-testid="jobsearch-JobComponent-description"]')
        if description_element:
            item['description'] = self.clean_html(' '.join(description_element.css('::text').getall()))
        else:
            item['description'] = ""
        
        # Job type
        job_type_elements = response.css('span[data-testid="attribute_snippet_testid"]::text').getall()
        item['job_type'] = ', '.join([jt for jt in job_type_elements if 'time' in jt.lower()]) or "Full-time"
        
        # URLs and IDs
        item['job_url'] = response.url
        item['job_id'] = self.extract_job_id(response.url)
        
        # Apply URL - check for Indeed Apply vs external
        apply_button = response.css('div[data-testid="applyButtonLinkContainer"] a::attr(href)').get()
        if apply_button:
            item['apply_url'] = response.urljoin(apply_button)
            item['easy_apply_available'] = 'indeedApply' in apply_button
        else:
            item['apply_url'] = ""
            item['easy_apply_available'] = False
        
        # Company URL
        company_link = response.css('div[data-testid="inlineHeader-companyName"] a::attr(href)').get()
        if company_link:
            item['company_url'] = response.urljoin(company_link)
        
        # Posted date
        posted_element = response.css('span[data-testid="myJobsStateDate"]::text').get()
        item['posted_date'] = self.parse_posted_date(posted_element)
        
        # Metadata
        item['source'] = 'Indeed'
        item['scraped_date'] = datetime.now().isoformat()
        
        # Analysis
        item['keywords'] = self.extract_keywords(item['description'])
        item['experience_level'] = self.determine_experience_level(item['title'], item['description'])
        item['remote_friendly'] = self.is_remote_job(item['location'], item['description'])
        item['priority_score'] = self.calculate_priority_score(item)
        
        # Auto-application analysis
        item['auto_apply_eligible'] = self.check_auto_apply_eligibility(item)
        item['application_complexity'] = self.assess_application_complexity(item)
        item['application_method'] = self.determine_application_method(item)
        
        # Initialize application status
        item['application_status'] = 'Not Applied'
        item['notes'] = ''
        
        yield item
    
    def get_headers(self):
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    def clean_html(self, text):
        if not text:
            return ""
        
        import re
        from html import unescape
        
        # Remove HTML tags and clean up
        clean_text = re.sub(r'<[^>]+>', ' ', text)
        clean_text = unescape(clean_text)
        clean_text = re.sub(r'\s+', ' ', clean_text)
        return clean_text.strip()
    
    def extract_job_id(self, url):
        match = re.search(r'jk=([^&]+)', url)
        return match.group(1) if match else ""
    
    def parse_posted_date(self, posted_text):
        if not posted_text:
            return ""
        
        # Parse "Posted X days ago" format
        if 'day' in posted_text.lower():
            days_match = re.search(r'(\d+)', posted_text)
            if days_match:
                days_ago = int(days_match.group(1))
                posted_date = datetime.now() - timedelta(days=days_ago)
                return posted_date.isoformat()
        
        return datetime.now().isoformat()
    
    def extract_keywords(self, text):
        if not text:
            return []
        
        tech_keywords = [
            'Python', 'SQL', 'Java', 'Scala', 'R', 'JavaScript',
            'AWS', 'GCP', 'Azure', 'Docker', 'Kubernetes',
            'TensorFlow', 'PyTorch', 'Spark', 'Hadoop', 'Airflow',
            'dbt', 'Snowflake', 'BigQuery', 'Redshift', 'Databricks',
            'Machine Learning', 'Deep Learning', 'MLOps', 'CI/CD',
            'Git', 'Linux', 'NoSQL', 'MongoDB', 'Elasticsearch'
        ]
        
        found_keywords = []
        text_lower = text.lower()
        
        for keyword in tech_keywords:
            if keyword.lower() in text_lower:
                found_keywords.append(keyword)
        
        return found_keywords
    
    def determine_experience_level(self, title, description):
        content = f"{title} {description}".lower()
        
        senior_patterns = ['senior', 'lead', 'principal', 'staff', '5+ years', '6+ years', 'expert']
        junior_patterns = ['junior', 'entry', 'associate', 'new grad', '0-2 years', '1-3 years']
        
        if any(pattern in content for pattern in senior_patterns):
            return 'Senior'
        elif any(pattern in content for pattern in junior_patterns):
            return 'Junior'
        else:
            return 'Mid-Level'
    
    def is_remote_job(self, location, description):
        location_lower = location.lower() if location else ""
        description_lower = description.lower() if description else ""
        
        remote_indicators = ['remote', 'work from home', 'distributed', 'anywhere']
        
        return any(indicator in location_lower or indicator in description_lower 
                  for indicator in remote_indicators)
    
    def calculate_priority_score(self, item):
        score = 0
        
        # Company tier
        tier1_companies = ['Google', 'Apple', 'Microsoft', 'Amazon', 'Meta', 'Netflix']
        tier2_companies = ['Uber', 'Airbnb', 'Stripe', 'Spotify', 'Twitter', 'Salesforce']
        
        company = item.get('company', '').lower()
        if any(comp.lower() in company for comp in tier1_companies):
            score += 25
        elif any(comp.lower() in company for comp in tier2_companies):
            score += 15
        
        # Keyword relevance
        keywords = item.get('keywords', [])
        preferred_keywords = ['Python', 'Machine Learning', 'AWS', 'Docker', 'TensorFlow']
        matched_keywords = [k for k in keywords if k in preferred_keywords]
        score += len(matched_keywords) * 3
        
        # Remote work
        if item.get('remote_friendly'):
            score += 8
        
        # Salary transparency
        if item.get('salary') and item.get('salary').strip():
            score += 5
        
        # Easy apply bonus
        if item.get('easy_apply_available'):
            score += 3
        
        # Recent posting
        if item.get('posted_date'):
            posted_date = datetime.fromisoformat(item['posted_date'].replace('Z', '+00:00'))
            days_old = (datetime.now() - posted_date.replace(tzinfo=None)).days
            if days_old <= 2:
                score += 5
        
        return min(score, 50)
    
    def check_auto_apply_eligibility(self, item):
        """Determine if job is eligible for auto-application"""
        
        # Must have easy apply
        if not item.get('easy_apply_available'):
            return False
        
        # Must be high priority
        if item.get('priority_score', 0) < 20:
            return False
        
        # Must not require complex application (portfolio, etc.)
        description = item.get('description', '').lower()
        complex_indicators = ['portfolio', 'cover letter required', 'writing sample', 'references']
        if any(indicator in description for indicator in complex_indicators):
            return False
        
        # Must match keywords
        keywords = item.get('keywords', [])
        required_keywords = os.getenv('JOB_KEYWORDS', '').split(',')
        if not any(req.strip().lower() in ' '.join(keywords).lower() for req in required_keywords):
            return False
        
        return True
    
    def assess_application_complexity(self, item):
        """Assess how complex the application process is"""
        
        if item.get('easy_apply_available'):
            return 'Simple'
        
        description = item.get('description', '').lower()
        
        if any(word in description for word in ['portfolio', 'cover letter', 'writing sample']):
            return 'Complex'
        elif any(word in description for word in ['resume', 'cv', 'application']):
            return 'Medium'
        else:
            return 'Unknown'
    
    def determine_application_method(self, item):
        """Determine the best application method"""
        
        if item.get('easy_apply_available'):
            return 'Indeed Easy Apply'
        elif item.get('apply_url'):
            return 'External Website'
        else:
            return 'Manual Research Required'
