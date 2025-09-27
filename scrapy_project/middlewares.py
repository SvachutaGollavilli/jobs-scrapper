from scrapy_selenium import SeleniumRequest, SeleniumMiddleware
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random

class CustomSeleniumMiddleware(SeleniumMiddleware):
    
    def process_request(self, request, spider):
        if not isinstance(request, SeleniumRequest):
            return None
            
        # Add random delays and human-like behavior
        if hasattr(spider, 'custom_settings'):
            delay = spider.custom_settings.get('DOWNLOAD_DELAY', 3)
            time.sleep(delay + random.uniform(0, 2))
        
        return super().process_request(request, spider)

class AntiDetectionMiddleware:
    
    def process_request(self, request, spider):
        # Add headers to appear more human-like
        request.headers.setdefault('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8')
        request.headers.setdefault('Accept-Language', 'en-US,en;q=0.5')
        request.headers.setdefault('Accept-Encoding', 'gzip, deflate')
        request.headers.setdefault('Connection', 'keep-alive')
        request.headers.setdefault('Upgrade-Insecure-Requests', '1')
        
        return None
