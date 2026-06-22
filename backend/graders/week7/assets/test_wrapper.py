import json
import os
import sys
import subprocess
import glob

def grade():
    breakdown = {
        "execution": 0,
        "files_created": 0,
        "json_structure": 0
    }
    feedback_messages = []
    REPO_DIR = os.getcwd()

    # Verify collect_wiki.py exists
    if not os.path.exists("collect_wiki.py"):
        feedback_messages.append("Error: collect_wiki.py not found in the root of the repository.")
        print(json.dumps({"breakdown": breakdown, "feedback": feedback_messages}))
        return

    # Install requests/beautifulsoup4 in case they didn't, or just rely on standard library?
    # Usually we pre-install or we let them provide requirements.txt. For safety, let's just run it.
    if os.path.exists("requirements.txt"):
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], capture_output=True, cwd=REPO_DIR)
    else:
        # Fallback install requests and bs4
        subprocess.run([sys.executable, "-m", "pip", "install", "requests", "beautifulsoup4"], capture_output=True, cwd=REPO_DIR)

    # A. Execution (30 pts)
    try:
        proc = subprocess.run(
            [sys.executable, "collect_wiki.py", "urls.txt"],
            capture_output=True,
            text=True,
            timeout=25,
            cwd=REPO_DIR
        )
        if proc.returncode == 0:
            breakdown["execution"] = 30
            feedback_messages.append("Execution (30/30): Script ran and exited successfully.")
        else:
            feedback_messages.append(f"Execution (0/30): Script failed with exit code {proc.returncode}. Error: {proc.stderr[:200]}")
    except subprocess.TimeoutExpired:
        feedback_messages.append("Execution (0/30): Script timed out after 25 seconds.")
    except Exception as e:
        feedback_messages.append(f"Execution (0/30): Failed to execute: {e}")

    # B. Files Created (40 pts)
    # Check if JSON files were created
    json_files = glob.glob("*.json")
    if len(json_files) >= 2:
        breakdown["files_created"] = 40
        feedback_messages.append(f"Files Created (40/40): Found {len(json_files)} JSON files.")
    elif len(json_files) > 0:
        breakdown["files_created"] = 20
        feedback_messages.append(f"Files Created (20/40): Found {len(json_files)} JSON files, but expected at least 2.")
    else:
        feedback_messages.append("Files Created (0/40): No JSON files found after execution.")

    # C. JSON Structure (30 pts)
    structure_score = 0
    if len(json_files) > 0:
        valid_files = 0
        for jf in json_files:
            try:
                with open(jf, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if "url" in data and "title" in data and "content" in data:
                    valid_files += 1
            except Exception:
                pass
        
        if valid_files == len(json_files):
            breakdown["json_structure"] = 30
            feedback_messages.append("JSON Structure (30/30): All JSON files have required keys (url, title, content).")
        elif valid_files > 0:
            breakdown["json_structure"] = 15
            feedback_messages.append(f"JSON Structure (15/30): Only {valid_files} JSON files had correct structure.")
        else:
            feedback_messages.append("JSON Structure (0/30): None of the JSON files had the required keys.")

    print(json.dumps({"breakdown": breakdown, "feedback": feedback_messages}))

if __name__ == "__main__":
    grade()
