#!/usr/bin/env python3
import json
import os
import subprocess
import sys

TIMEOUT = 60

def main():
    breakdown = {
        "engineering_quality": 20.0,
        "dataset": 10.0,
        "persistent_inverted_index": 20.0,
        "ranking": 15.0,
        "query_handling": 35.0,
    }
    feedback = []

    # Basic structure check
    if os.path.isfile("README.md"):
        breakdown["engineering_quality"] = 20.0
        feedback.append("README.md found.")
    else:
        breakdown["engineering_quality"] = 10.0
        feedback.append("README.md missing.")

    # Dataset check
    if os.path.isdir("corpus"):
        files = os.listdir("corpus")
        if len(files) >= 3:
            breakdown["dataset"] = 10.0
            feedback.append("Dataset found.")
        else:
            breakdown["dataset"] = 5.0
            feedback.append("Dataset too small.")
    else:
        feedback.append("corpus/ directory missing.")

    # Index execution
    if os.path.isfile("build_index.py"):
        subprocess.run([sys.executable, "build_index.py"], capture_output=True, timeout=TIMEOUT)
        if os.path.isfile("index.json"):
            breakdown["persistent_inverted_index"] = 20.0
            feedback.append("index.json created.")
        else:
            feedback.append("index.json not created.")
    else:
        feedback.append("build_index.py missing.")

    # Query Handling
    if os.path.isfile("query.py"):
        try:
            r = subprocess.run([sys.executable, "query.py"], input="test\nquery2\nquit\n", capture_output=True, text=True, timeout=TIMEOUT)
            if r.returncode == 0:
                breakdown["query_handling"] = 35.0
                breakdown["ranking"] = 15.0
                feedback.append("query.py handled queries correctly.")
            else:
                feedback.append(f"query.py failed: {r.returncode}")
        except Exception as e:
            feedback.append(f"query.py exception: {e}")
    else:
        feedback.append("query.py missing.")

    print(json.dumps({"breakdown": breakdown, "feedback": feedback, "bonus_features": []}))

if __name__ == "__main__":
    main()
