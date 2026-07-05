#!/usr/bin/env python3
import json
import os
import subprocess
import sys

SCRIPT = "query.py"
TIMEOUT = 30

def main():
    breakdown = {
        "execution": 0.0,
        "multi_word_query": 0.0,
        "boolean_operators": 0.0,
    }
    feedback = []

    if not os.path.isfile(SCRIPT):
        feedback.append(f"{SCRIPT} missing.")
        print(json.dumps({"breakdown": breakdown, "feedback": feedback, "bonus_features": []}))
        return

    # Anti-spoof check
    try:
        r_spoof = subprocess.run([sys.executable, SCRIPT], input="asdfasdfasdf\\nquit\\n", capture_output=True, text=True, timeout=TIMEOUT)
        out_lower_spoof = r_spoof.stdout.lower()
        if "page1" in out_lower_spoof or "page2" in out_lower_spoof:
            feedback.append("Execution failed: script unconditionally returned documents for invalid query.")
            print(json.dumps({"breakdown": breakdown, "feedback": feedback, "bonus_features": []}))
            return
    except Exception:
        pass

    # Basic execution
    try:
        r = subprocess.run([sys.executable, SCRIPT], input="python\nquit\n", capture_output=True, text=True, timeout=TIMEOUT)
        if r.returncode == 0:
            breakdown["execution"] = 30.0
            feedback.append("Execution successful.")
        else:
            feedback.append(f"Execution failed with code {r.returncode}.")
    except Exception as e:
        feedback.append(f"Execution failed: {e}")

    # Multi-word
    try:
        r = subprocess.run([sys.executable, SCRIPT], input="programming language\nquit\n", capture_output=True, text=True, timeout=TIMEOUT)
        corpus_files = [f.lower() for f in os.listdir("corpus")] if os.path.isdir("corpus") else []
        out_lower = r.stdout.lower()
        valid_doc_found = "page1" in out_lower
        
        if r.returncode == 0 and valid_doc_found:
            breakdown["multi_word_query"] = 35.0
            feedback.append("Multi-word query successful.")
        else:
            feedback.append("Multi-word query failed or returned no docs.")
    except Exception as e:
        feedback.append(f"Multi-word query failed: {e}")

    # Boolean
    try:
        r = subprocess.run([sys.executable, SCRIPT], input="python AND linux\nquit\n", capture_output=True, text=True, timeout=TIMEOUT)
        out_lower = r.stdout.lower()
        valid_doc_found = "page1" in out_lower
        
        if r.returncode == 0 and (valid_doc_found or "not found" in out_lower or "0 document" in out_lower):
            breakdown["boolean_operators"] = 35.0
            feedback.append("Boolean operators handled.")
        else:
            feedback.append("Boolean operators failed.")
    except Exception as e:
        feedback.append(f"Boolean operators failed: {e}")

    print(json.dumps({"breakdown": breakdown, "feedback": feedback, "bonus_features": []}))

if __name__ == "__main__":
    main()
