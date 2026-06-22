import json
import os
import sys
import subprocess

def grade():
    breakdown = {
        "build_index": 0,
        "lookup": 0
    }
    feedback_messages = []
    REPO_DIR = os.getcwd()

    if not os.path.exists("build_index.py") or not os.path.exists("lookup.py"):
        feedback_messages.append("Error: build_index.py or lookup.py not found.")
        print(json.dumps({"breakdown": breakdown, "feedback": feedback_messages}))
        return

    # 1. Build Index (50 pts)
    try:
        proc = subprocess.run(
            [sys.executable, "build_index.py", "test_corpus", "index.json"],
            capture_output=True,
            text=True,
            timeout=15,
            cwd=REPO_DIR
        )
        if proc.returncode == 0 and os.path.exists("index.json"):
            breakdown["build_index"] = 50
            feedback_messages.append("Build Index (50/50): Successfully built index.json.")
        else:
            feedback_messages.append(f"Build Index (0/50): Failed to build index. Exit code {proc.returncode}.")
    except Exception as e:
        feedback_messages.append(f"Build Index (0/50): Failed with error: {e}")

    # 2. Lookup (50 pts)
    if os.path.exists("index.json"):
        try:
            proc = subprocess.run(
                [sys.executable, "lookup.py", "index.json", "mock"],
                capture_output=True,
                text=True,
                timeout=15,
                cwd=REPO_DIR
            )
            if proc.returncode == 0 and "mock" in proc.stdout.lower():
                breakdown["lookup"] = 50
                feedback_messages.append("Lookup (50/50): Successfully found 'mock' in index.")
            else:
                feedback_messages.append("Lookup (0/50): Did not output expected results for query 'mock'.")
        except Exception as e:
            feedback_messages.append(f"Lookup (0/50): Failed with error: {e}")

    print(json.dumps({"breakdown": breakdown, "feedback": feedback_messages}))

if __name__ == "__main__":
    grade()
