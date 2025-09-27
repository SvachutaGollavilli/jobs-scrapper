#!/usr/bin/env python3
import subprocess
import sys

def test_spider(spider_name):
    print(f"🧪 Testing {spider_name}...")
    
    try:
        result = subprocess.run([
            'scrapy', 'crawl', spider_name,
            '-s', 'CLOSESPIDER_ITEMCOUNT=5',
            '-o', f'test_{spider_name}.json'
        ], cwd='scrapy_project', capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ {spider_name} passed")
            return True
        else:
            print(f"❌ {spider_name} failed")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    spiders = ['indeed_jobs', 'linkedin_jobs']
    results = {}
    
    for spider in spiders:
        results[spider] = test_spider(spider)
    
    print("\n📊 Results:")
    for spider, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{spider}: {status}")
    
    if not all(results.values()):
        sys.exit(1)

if __name__ == "__main__":
    main()
