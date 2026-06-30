import json
import os
import sys
import subprocess
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

# Mock HTML content
MOCK_PAGES = {
    "/wiki/Python_(programming_language)": """
    <html>
        <head><title>Python (programming language) - Wikipedia</title></head>
        <body>
            <p>Python is a high-level, general-purpose programming language.</p>
        </body>
    </html>
    """,
    "/wiki/Linux": """
    <html>
        <head><title>Linux - Wikipedia</title></head>
        <body>
            <p>Linux is a family of open-source Unix-like operating systems.</p>
        </body>
    </html>
    """
}

class MockWikiHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in MOCK_PAGES:
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(MOCK_PAGES[self.path].encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")
            
    def log_message(self, format, *args):
        pass # Suppress logging

def start_server():
    server = HTTPServer(('127.0.0.1', 8080), MockWikiHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server

def grade():
    breakdown = {
        "execution": 0,
        "corpus_dir": 0,
        "json_schema": 0,
        "content_extraction": 0
    }
    feedback = []
    
    server = start_server()
    time.sleep(0.5)
    
    # Write urls.txt
    urls = [
        "http://127.0.0.1:8080/wiki/Python_(programming_language)",
        "http://127.0.0.1:8080/wiki/Linux"
    ]
    with open("urls.txt", "w") as f:
        f.write("\n".join(urls) + "\n")
        
    # Execute collect_wiki.py
    try:
        proc = subprocess.run(
            [sys.executable, "collect_wiki.py"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if proc.returncode == 0:
            breakdown["execution"] = 20
            feedback.append("Execution (20/20): collect_wiki.py ran successfully.")
        else:
            feedback.append(f"Execution (0/20): Script exited with non-zero code {proc.returncode}.")
            print(json.dumps({"breakdown": breakdown, "feedback": feedback}))
            return
    except subprocess.TimeoutExpired:
        feedback.append("Execution (0/20): Script timed out.")
        print(json.dumps({"breakdown": breakdown, "feedback": feedback}))
        return
    except Exception as e:
        feedback.append(f"Execution (0/20): Failed to run script: {e}")
        print(json.dumps({"breakdown": breakdown, "feedback": feedback}))
        return
        
    # Check corpus directory
    if os.path.exists("corpus") and os.path.isdir("corpus"):
        breakdown["corpus_dir"] = 20
        feedback.append("Corpus Directory (20/20): Found 'corpus' directory.")
    else:
        feedback.append("Corpus Directory (0/20): 'corpus' directory not found.")
        print(json.dumps({"breakdown": breakdown, "feedback": feedback}))
        return
        
    # Check JSON files
    json_files = [f for f in os.listdir("corpus") if f.endswith(".json")]
    if len(json_files) == 2:
        schema_passed = True
        content_passed = True
        for jfile in json_files:
            with open(os.path.join("corpus", jfile), "r") as f:
                try:
                    data = json.load(f)
                    # Check schema
                    keys = set(data.keys())
                    expected_keys = {"title", "url", "text", "fetched_at"}
                    if not expected_keys.issubset(keys):
                        schema_passed = False
                    
                    # Check content
                    if "Python" in data.get("title", "") or "Linux" in data.get("title", ""):
                        pass
                    else:
                        content_passed = False
                        
                    text = data.get("text", "")
                    if "programming language" not in text and "operating systems" not in text:
                        content_passed = False
                        
                except Exception:
                    schema_passed = False
                    content_passed = False
                    
        if schema_passed:
            breakdown["json_schema"] = 30
            feedback.append("JSON Schema (30/30): Files have {title, url, text, fetched_at} keys.")
        else:
            feedback.append("JSON Schema (0/30): Missing expected keys in JSON files.")
            
        if content_passed:
            breakdown["content_extraction"] = 30
            feedback.append("Content Extraction (30/30): Successfully extracted plain text and title.")
        else:
            feedback.append("Content Extraction (0/30): Failed to extract correct text or title.")
    else:
        feedback.append(f"JSON Output (0/60): Expected 2 JSON files, found {len(json_files)}.")

    print(json.dumps({"breakdown": breakdown, "feedback": feedback}))

if __name__ == "__main__":
    grade()
