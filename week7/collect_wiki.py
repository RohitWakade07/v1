import sys
import json
import urllib.request
from urllib.error import URLError, HTTPError
import os
import re

def scrape_wiki(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8')
            
            # Very basic title extraction
            title_match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE)
            title = title_match.group(1).replace(' - Wikipedia', '') if title_match else "Unknown Title"
            
            # Extract paragraphs
            paragraphs = re.findall(r'<p>(.*?)</p>', html, re.DOTALL | re.IGNORECASE)
            text = " ".join(paragraphs)
            # Remove HTML tags
            text = re.sub(r'<[^>]+>', '', text)
            # Remove references like [1]
            text = re.sub(r'\[\d+\]', '', text)
            
            return {
                "title": title.strip(),
                "url": url,
                "text": text.strip()
            }
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python collect_wiki.py <urls_file>")
        sys.exit(1)
        
    try:
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            urls = f.read().splitlines()
    except Exception as e:
        print(f"Error reading URLs file: {e}")
        sys.exit(1)
        
    os.makedirs("corpus", exist_ok=True)
    
    for url in urls:
        url = url.strip()
        if not url: continue
        
        print(f"Scraping {url}...")
        data = scrape_wiki(url)
        if data and len(data["text"].split()) >= 50:
            slug = url.rstrip('/').split('/')[-1]
            if not slug:
                slug = "index"
            filepath = os.path.join("corpus", f"{slug}.json")
            with open(filepath, "w", encoding="utf-8") as out:
                json.dump(data, out, ensure_ascii=False, indent=2)
        else:
            print(f"Failed to extract meaningful content from {url}")

if __name__ == '__main__':
    main()
