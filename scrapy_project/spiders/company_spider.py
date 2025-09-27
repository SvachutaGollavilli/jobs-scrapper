import scrapy
from scrapy import Request
from scrapy_project.items import JobItem
from datetime import datetime
import re
import json

class CompanySpider(scrapy.Spider):
    name = 'company_spider'
    
    custom_settings = {
        'DOWNLOAD_DELAY': 2,
        'CONCURRENT_REQUESTS': 3,
    }
    
    # Add company career page URLs here
    start_urls = [
        'https://careers.google.com/jobs/results/',
        'https://jobs.netflix.com/search?q=engineer',
        'https://www.amazon.jobs/en/search.json?base_query=engineer',
    ]
    
    def parse(self, response):
        """Parse company job listings"""
        
        # Check if it's a JSON response (like Amazon)
        if 'application/json' in response.headers.get('Content-Type', b'').decode():
            yield from self.parse_json_jobs(response)
        else:
            # HTML response (like Google, Netflix)
            yield from self.parse_html_jobs(response)
    
    def parse_json_jobs(self, response):
        """Parse JSON format job listings"""
        try:
            data = json.loads(response.text)
            jobs = data.get('jobs', [])
            
            for job in jobs[:50]:  # Limit to 50 jobs
                item = JobItem()
                
                item['title'] = job.get('title', '')
                item['company'] = job.get('company_name', 'Amazon')
                item['location'] = job.get('location', '')
                item['job_url'] = job.get('job_path', '')
                item['description'] = job.get('description', '')
                item['posted_date'] = job.get('posted_date', '')
                item['source'] = 'Company Career Page'
                item['scraped_date'] = datetime.now().isoformat()
                
                # Basic analysis
                item['keywords'] = self.extract_keywords(item['description'])
                item['experience_level'] = self.determine_experience_level(item['title'])
                item['remote_friendly'] = 'remote' in item['location'].lower()
                item['priority_score'] = 20  # Company direct applications get bonus
                item['application_status'] = 'Not Applied'
                item['auto_apply_eligible'] = False
                item['application_method'] = 'Company Website'
                
                yield item
                
        except Exception as e:
            self.logger.error(f"Error parsing JSON jobs: {e}")
    
    def parse_html_jobs(self, response):
        """Parse HTML format job listings"""
        
        # Generic job card selectors (works for many sites)
        job_selectors = [
            '.job-tile',
            '.job-card',
            '[data-job-id]',
            '.career-item',
            '.position-card'
        ]
        
        jobs_found = []
        
        for selector in job_selectors:
            jobs_found = response.css(selector)
            if jobs_found:
                self.logger.info(f"Found {len(jobs_found)} jobs with selector: {selector}")
                break
        
        if not jobs_found:
            self.logger.warning(f"No jobs found on {response.url}")
            return
        
        for job in jobs_found[:50]:  # Limit to 50 jobs
            item = JobItem()
            
            # Try multiple selectors for each field
            item['title'] = (
                job.css('.job-title::text').get() or
                job.css('h3::text').get() or
                job.css('[data-job-title]::text').get() or
                ''
            ).strip()
            
            item['company'] = (
                job.css('.company-name::text').get() or
                self.extract_company_from_url(response.url) or
                'Unknown'
            ).strip()
            
            item['location'] = (
                job.css('.location::text').get() or
                job.css('[data-location]::text').get() or
                ''
            ).strip()
            
            job_link = (
                job.css('a::attr(href)').get() or
                job.css('[data-job-url]::attr(href)').get() or
                ''
            )
            item['job_url'] = response.urljoin(job_link) if job_link else response.url
            
            # Description (may need to visit detail page)
            description = job.css('.description::text').get() or ''
            item['description'] = description.strip()
            
            # If description is short, try to get more details
            if len(description) < 100 and job_link:
                yield Request(
                    url=response.urljoin(job_link),
                    callback=self.parse_job_detail,
                    meta={'item': item}
                )
                continue
            
            # Metadata
            item['source'] = 'Company Career Page'
            item['scraped_date'] = datetime.now().isoformat()
            item['posted_date'] = ''
            
            # Analysis
            item['keywords'] = self.extract_keywords(item['description'])
            item['experience_level'] = self.determine_experience_level(item['title'])
            item['remote_friendly'] = 'remote' in item['location'].lower()
            item['priority_score'] = 20
            item['application_status'] = 'Not Applied'
            item['auto_apply_eligible'] = False
            item['application_method'] = 'Company Website'
            
            yield item
    
    def parse_job_detail(self, response):
        """Parse individual job detail page"""
        item = response.meta['item']
        
        # Get full description
        description_selectors = [
            '.job-description',
            '[data-description]',
            '.job-details',
            '.description-content'
        ]
        
        for selector in description_selectors:
            desc_element = response.css(selector)
            if desc_element:
                item['description'] = ' '.join(desc_element.css('::text').getall()).strip()
                break
        
        # Update analysis with full description
        item['keywords'] = self.extract_keywords(item['description'])
        
        yield item
    
    def extract_company_from_url(self, url):
        """Extract company name from URL"""
        # careers.google.com -> Google
        # jobs.netflix.com -> Netflix
        # amazon.jobs -> Amazon
        
        patterns = [
            r'careers\.([^.]+)\.',
            r'jobs\.([^.]+)\.',
            r'([^.]+)\.jobs',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1).title()
        
        return 'Unknown'
    
    def extract_keywords(self, text):
        """Extract technical keywords from text"""
        if not text:
            return []
        
        keywords = [
            'Python', 'Java', 'JavaScript', 'SQL', 'C++',
            'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes',
            'Machine Learning', 'AI', 'Data Science',
            'React', 'Node.js', 'Django', 'Flask'
        ]
        
        found = []
        text_lower = text.lower()
        
        for keyword in keywords:
            if keyword.lower() in text_lower:
                found.append(keyword)
        
        return found
    
    def determine_experience_level(self, title):
        """Determine experience level from job title"""
        title_lower = title.lower()
        
        if any(word in title_lower for word in ['senior', 'lead', 'principal', 'staff']):
            return 'Senior'
        elif any(word in title_lower for word in ['junior', 'entry', 'associate']):
            return 'Junior'
        else:
            return 'Mid-Level'
