import sys
import json
import urllib.request

def main():
    if len(sys.argv) < 2:
        sys.exit(1)
        
    with open(sys.argv[1], "r") as f:
        urls = f.read().splitlines()
        
    for i, url in enumerate(urls):
        if not url.strip(): continue
        # Mock fetching
        data = {
            "url": url,
            "title": f"Mock Title {i}",
            "content": "Mock content for Wikipedia page."
        }
        with open(f"page_{i}.json", "w", encoding="utf-8") as out:
            json.dump(data, out)

if __name__ == "__main__":
    main()
