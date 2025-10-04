BOT_NAME = 'job_scraper'
SPIDER_MODULES = ['scrapy_project.spiders']
NEWSPIDER_MODULE = 'scrapy_project.spiders'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False  # Set to False for aggressive scraping

# Configure delays for different sites
DOWNLOAD_DELAY = 3
RANDOMIZE_DOWNLOAD_DELAY = True
CONCURRENT_REQUESTS = 4
CONCURRENT_REQUESTS_PER_DOMAIN = 1

# Auto-throttling
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0

# Disable cookies (avoid tracking)
COOKIES_ENABLED = False
TELNETCONSOLE_ENABLED = False

# Middleware configuration
DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    'scrapy_user_agents.middlewares.RandomUserAgentMiddleware': 400,
    'rotating_proxies.middlewares.RotatingProxyMiddleware': 610,
    'rotating_proxies.middlewares.BanDetectionMiddleware': 620,
    'scrapy_project.middlewares.CustomSeleniumMiddleware': 800,
}

# Item pipelines
ITEM_PIPELINES = {
    'scrapy_project.pipelines.DuplicatesPipeline': 200,
    'scrapy_project.pipelines.DataCleaningPipeline': 300,
    'scrapy_project.pipelines.AutoApplicationPipeline': 350,
    'scrapy_project.pipelines.GoogleSheetsPipeline': 400,
}

# Selenium settings
SELENIUM_DRIVER_NAME = 'chrome'
SELENIUM_DRIVER_EXECUTABLE_PATH = None
SELENIUM_DRIVER_ARGUMENTS = [
    '--headless=new',
    '--no-sandbox',
    '--disable-dev-shm-usage',
    '--disable-blink-features=AutomationControlled',
    '--disable-extensions',
    '--disable-plugins',
    '--disable-images',
    '--window-size=1920,1080',
    '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
]

# Proxy settings (optional)
ROTATING_PROXY_LIST_PATH = 'proxy_list.txt'

# Cache settings
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 3600

