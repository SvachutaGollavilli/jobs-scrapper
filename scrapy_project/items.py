import scrapy

class JobItem(scrapy.Item):
    # Basic information
    job_id = scrapy.Field()
    title = scrapy.Field()
    company = scrapy.Field()
    location = scrapy.Field()
    salary = scrapy.Field()
    job_type = scrapy.Field()
    
    # URLs
    job_url = scrapy.Field()
    apply_url = scrapy.Field()
    company_url = scrapy.Field()
    
    # Content
    description = scrapy.Field()
    requirements = scrapy.Field()
    responsibilities = scrapy.Field()
    benefits = scrapy.Field()
    
    # Metadata
    posted_date = scrapy.Field()
    scraped_date = scrapy.Field()
    source = scrapy.Field()
    
    # Analysis
    keywords = scrapy.Field()
    experience_level = scrapy.Field()
    remote_friendly = scrapy.Field()
    priority_score = scrapy.Field()
    match_score = scrapy.Field()
    
    # Application tracking
    application_status = scrapy.Field()
    application_method = scrapy.Field()
    auto_apply_eligible = scrapy.Field()
    application_complexity = scrapy.Field()
    notes = scrapy.Field()
    
    # Auto-application data
    email_found = scrapy.Field()
    contact_email = scrapy.Field()
    application_deadline = scrapy.Field()
    easy_apply_available = scrapy.Field()

