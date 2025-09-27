# Automatically update proxy list from free sources

import requests
import re
from datetime import datetime
import time
import random

def fetch_free_proxies():
    """Fetch fresh proxies from multiple free sources"""
    proxies = []
    
    print(f"🔄 Updating proxy list at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Source 1: Free Proxy List
    try:
        print("📥 Fetching from free-proxy-list.net...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get('https://free-proxy-list.net/', headers=headers, timeout=10)
        
        # Extract IP:Port pairs
        pattern = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})</td><td>(\d{2,5})</td>'
        matches = re.findall(pattern, response.text)
        
        for ip, port in matches[:50]:  # Take first 50
            proxies.append(f"{ip}:{port}")
        
        print(f"✅ Found {len(matches)} proxies from free-proxy-list.net")
        time.sleep(1)  # Be polite
        
    except Exception as e:
        print(f"❌ Error fetching from free-proxy-list.net: {e}")
    
    # Source 2: Proxy List Download
    try:
        print("📥 Fetching from proxy-list.download...")
        response = requests.get(
            'https://www.proxy-list.download/api/v1/get?type=http',
            timeout=10
        )
        proxy_lines = response.text.strip().split('\n')
        
        for line in proxy_lines[:30]:  # Take first 30
            line = line.strip()
            if ':' in line and len(line.split(':')) == 2:
                proxies.append(line)
        
        print(f"✅ Found {len(proxy_lines)} proxies from proxy-list.download")
        time.sleep(1)
        
    except Exception as e:
        print(f"❌ Error fetching from proxy-list.download: {e}")
    
    # Source 3: PubProxy API
    try:
        print("📥 Fetching from pubproxy.com...")
        response = requests.get(
            'http://pubproxy.com/api/proxy?limit=20&format=txt&type=http',
            timeout=10
        )
        proxy_lines = response.text.strip().split('\n')
        
        for line in proxy_lines:
            line = line.strip()
            if ':' in line:
                proxies.append(line)
        
        print(f"✅ Found {len(proxy_lines)} proxies from pubproxy.com")
        time.sleep(1)
        
    except Exception as e:
        print(f"❌ Error fetching from pubproxy.com: {e}")
    
    # Source 4: ProxyScrape
    try:
        print("📥 Fetching from proxyscrape.com...")
        response = requests.get(
            'https://api.proxyscrape.com/v2/?request=get&protocol=http&timeout=5000&country=all&simplified=true',
            timeout=10
        )
        proxy_lines = response.text.strip().split('\n')
        
        for line in proxy_lines[:30]:
            line = line.strip()
            if ':' in line:
                proxies.append(line)
        
        print(f"✅ Found {len(proxy_lines)} proxies from proxyscrape.com")
        time.sleep(1)
        
    except Exception as e:
        print(f"❌ Error fetching from proxyscrape.com: {e}")
    
    # Source 5: GeoNode
    try:
        print("📥 Fetching from geonode.com...")
        response = requests.get(
            'https://proxylist.geonode.com/api/proxy-list?limit=50&page=1&sort_by=lastChecked&sort_type=desc',
            timeout=10
        )
        data = response.json()
        
        if 'data' in data:
            for proxy in data['data']:
                ip = proxy.get('ip')
                port = proxy.get('port')
                if ip and port:
                    proxies.append(f"{ip}:{port}")
        
        print(f"✅ Found {len(data.get('data', []))} proxies from geonode.com")
        
    except Exception as e:
        print(f"❌ Error fetching from geonode.com: {e}")
    
    # Remove duplicates and invalid entries
    proxies = list(set(proxies))
    
    # Filter out obviously invalid proxies
    valid_proxies = []
    for proxy in proxies:
        parts = proxy.split(':')
        if len(parts) == 2:
            ip, port = parts
            # Basic validation
            ip_parts = ip.split('.')
            if len(ip_parts) == 4 and all(p.isdigit() and 0 <= int(p) <= 255 for p in ip_parts):
                if port.isdigit() and 1 <= int(port) <= 65535:
                    valid_proxies.append(proxy)
    
    return valid_proxies

def validate_proxy(proxy, timeout=5):
    """Test if proxy is working"""
    try:
        proxies_dict = {
            'http': f'http://{proxy}',
            'https': f'http://{proxy}'
        }
        
        response = requests.get(
            'http://httpbin.org/ip',
            proxies=proxies_dict,
            timeout=timeout
        )
        
        if response.status_code == 200:
            return True
        return False
        
    except:
        return False

def test_proxies(proxies, max_test=20):
    """Test a subset of proxies"""
    print(f"\n🔍 Testing {min(max_test, len(proxies))} proxies...")
    
    valid_proxies = []
    test_count = min(max_test, len(proxies))
    
    # Randomly sample proxies to test
    test_proxies = random.sample(proxies, test_count)
    
    for i, proxy in enumerate(test_proxies, 1):
        print(f"Testing {i}/{test_count}: {proxy}...", end=' ')
        
        if validate_proxy(proxy, timeout=5):
            valid_proxies.append(proxy)
            print("✅")
        else:
            print("❌")
        
        time.sleep(0.5)  # Small delay to avoid rate limiting
    
    success_rate = (len(valid_proxies) / test_count) * 100 if test_count > 0 else 0
    print(f"\n📊 Validation Results: {len(valid_proxies)}/{test_count} working ({success_rate:.1f}%)")
    
    return valid_proxies

def save_proxies(proxies, filename='proxy_list.txt'):
    """Save proxies to file"""
    try:
        with open(filename, 'w') as f:
            # Write header
            f.write(f"# Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("# Free proxy list - Auto-updated\n")
            f.write("# Format: ip:port\n")
            f.write("# Sources: free-proxy-list.net, proxy-list.download, pubproxy.com, proxyscrape.com, geonode.com\n\n")
            
            # Write proxies
            for proxy in proxies:
                f.write(f"{proxy}\n")
        
        print(f"💾 Saved {len(proxies)} proxies to {filename}")
        return True
        
    except Exception as e:
        print(f"❌ Error saving proxies: {e}")
        return False

def get_proxy_stats(filename='proxy_list.txt'):
    """Get statistics about current proxy list"""
    try:
        with open(filename, 'r') as f:
            lines = f.readlines()
        
        proxies = [l.strip() for l in lines if ':' in l and not l.startswith('#')]
        
        if proxies:
            # Get last update time from file
            for line in lines:
                if line.startswith('# Updated:'):
                    update_time = line.replace('# Updated:', '').strip()
                    print(f"📅 Last updated: {update_time}")
                    break
            
            print(f"📊 Current proxy count: {len(proxies)}")
            
            # Check if proxies are old (older than 24 hours)
            try:
                with open(filename, 'r') as f:
                    first_line = f.readline()
                    if '# Updated:' in first_line:
                        update_time_str = first_line.split('# Updated:')[1].strip()
                        update_time = datetime.strptime(update_time_str, '%Y-%m-%d %H:%M:%S')
                        age_hours = (datetime.now() - update_time).total_seconds() / 3600
                        
                        if age_hours > 24:
                            print(f"⚠️  Proxies are {age_hours:.1f} hours old (update recommended)")
                        else:
                            print(f"✅ Proxies are fresh ({age_hours:.1f} hours old)")
            except:
                pass
        else:
            print("⚠️  No proxies found in file")
        
        return len(proxies)
        
    except FileNotFoundError:
        print("❌ Proxy list file not found")
        return 0

def main():
    """Main function to update proxy list"""
    print("🚀 Starting proxy updater...")
    print("=" * 60)
    
    # Show current stats
    print("\n📊 Current Proxy Status:")
    get_proxy_stats()
    
    print("\n" + "=" * 60)
    
    # Fetch new proxies
    print("\n🌐 Fetching new proxies from multiple sources...")
    proxies = fetch_free_proxies()
    
    if not proxies:
        print("❌ No proxies found!")
        return
    
    print(f"\n📊 Total proxies fetched: {len(proxies)}")
    
    # Optional: Validate proxies (uncomment to enable - makes process slower)
    # Validation is disabled by default for speed, but you can enable it for better quality
    
    validate = input("\n🔍 Validate proxies? (slower but more reliable) [y/N]: ").lower()
    
    if validate == 'y':
        valid_proxies = test_proxies(proxies, max_test=20)
        if valid_proxies:
            print(f"\n✅ Using {len(valid_proxies)} validated proxies")
            proxies = valid_proxies
        else:
            print("\n⚠️  No proxies passed validation, using all fetched proxies")
    else:
        print("\n⏭️  Skipping validation (faster but may include dead proxies)")
    
    # Save to file
    print("\n💾 Saving proxies to file...")
    if save_proxies(proxies):
        print("\n" + "=" * 60)
        print("✅ Proxy list updated successfully!")
        print(f"📊 Total proxies saved: {len(proxies)}")
        print(f"📁 File: proxy_list.txt")
        print("=" * 60)
    else:
        print("\n❌ Failed to update proxy list!")

if __name__ == "__main__":
    main()
