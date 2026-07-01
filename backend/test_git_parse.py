import re
from urllib.parse import urlparse

GITHUB_URL_PATTERN = re.compile(
    r"^https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)(?:\.git)?(?:/tree/([^/]+)/(.*))?$"
)

def parse_github_url(url: str):
    match = GITHUB_URL_PATTERN.match(url)
    if not match:
        raise ValueError(f"Invalid GitHub URL: {url}")
    
    owner = match.group(1)
    repo = match.group(2)
    # Group 3 is branch (if present), Group 4 is path (if present)
    branch = match.group(3)
    path = match.group(4)
    
    base_url = f"https://github.com/{owner}/{repo}.git"
    return {
        "base_url": base_url,
        "branch": branch,
        "path": path
    }

urls = [
    "https://github.com/torvalds/linux",
    "https://github.com/torvalds/linux.git",
    "https://github.com/torvalds/linux/tree/master/fs",
    "https://github.com/I-M-Sharma/eep1-grader/tree/main/week-06"
]

for u in urls:
    print(f"URL: {u}")
    try:
        print("Parsed:", parse_github_url(u))
    except Exception as e:
        print("Error:", e)
    print("-" * 40)
