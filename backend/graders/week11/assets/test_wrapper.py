#!/usr/bin/env python3
import json
import os
import subprocess
import sys

TIMEOUT = 60

def main():
    breakdown = {
        "engineering_quality": 0.0,
        "dataset": 0.0,
        "persistent_inverted_index": 0.0,
        "ranking": 0.0,
        "query_handling": 0.0,
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
        breakdown["dataset"] = 0.0
        feedback.append("corpus/ directory missing.")

    # Index execution
    if os.path.isfile("build_index.py"):
        subprocess.run([sys.executable, "build_index.py"], capture_output=True, timeout=TIMEOUT)
        if os.path.isfile("index.json"):
            breakdown["persistent_inverted_index"] = 20.0
            feedback.append("index.json created.")
        else:
            breakdown["persistent_inverted_index"] = 0.0
            feedback.append("index.json not created.")
    else:
        breakdown["persistent_inverted_index"] = 0.0
        feedback.append("build_index.py missing.")

    # Query Handling
    if os.path.isfile("query.py"):
        try:
            import pexpect
            child = pexpect.spawn(sys.executable, ["query.py"], timeout=5, encoding="utf-8")
            child.sendline("asdfasdfasdf")
            # Wait a short moment to let it process
            child.expect([pexpect.TIMEOUT, pexpect.EOF], timeout=1)
            out_lower_spoof = (child.before or "").lower()
            child.sendline("quit")
            child.close()
            
            corpus_files = [f.lower() for f in os.listdir("corpus")] if os.path.isdir("corpus") else []
            valid_doc_found = False
            for f in corpus_files:
                doc_name = f.replace(".json", "")
                if doc_name and doc_name != "doc" and (f in out_lower_spoof or doc_name in out_lower_spoof):
                    valid_doc_found = True
                    break
            
            if valid_doc_found:
                breakdown["query_handling"] = 0.0
                breakdown["ranking"] = 0.0
                feedback.append("query.py failed: unconditionally returned documents for invalid query.")
                print(json.dumps({"breakdown": breakdown, "feedback": feedback, "bonus_features": []}))
                return
        except Exception:
            pass

        try:
            import pexpect
            child = pexpect.spawn(sys.executable, ["query.py"], timeout=5, encoding="utf-8")
            
            # Send first query
            child.sendline("test")
            child.expect([pexpect.TIMEOUT, pexpect.EOF], timeout=1)
            out_test = (child.before or "").lower()
            
            # Send second query
            if child.isalive():
                child.sendline("query2")
                child.expect([pexpect.TIMEOUT, pexpect.EOF], timeout=1)
            out_query2 = (child.before or "").lower()
            
            # Send quit
            if child.isalive():
                child.sendline("quit")
                child.expect(pexpect.EOF, timeout=2)
                
            out_lower = out_test + out_query2
            valid_doc_found = False
            for f in corpus_files:
                doc_name = f.replace(".json", "")
                if doc_name and doc_name != "doc" and (f in out_lower or doc_name in out_lower):
                    valid_doc_found = True
                    break
            
            if valid_doc_found or "not found" in out_lower or "0 document" in out_lower:
                breakdown["query_handling"] = 35.0
                breakdown["ranking"] = 15.0
                feedback.append("query.py handled queries correctly.")
            else:
                breakdown["query_handling"] = 0.0
                breakdown["ranking"] = 0.0
                feedback.append("query.py failed to return valid document results.")
        except pexpect.exceptions.EOF:
            breakdown["query_handling"] = 0.0
            breakdown["ranking"] = 0.0
            feedback.append("query.py crashed with EOFError unexpectedly.")
        except pexpect.exceptions.TIMEOUT:
            breakdown["query_handling"] = 0.0
            breakdown["ranking"] = 0.0
            feedback.append("query.py timed out or did not exit cleanly on 'quit'.")
        except Exception as e:
            breakdown["query_handling"] = 0.0
            breakdown["ranking"] = 0.0
            feedback.append(f"query.py exception: {e}")
    else:
        breakdown["query_handling"] = 0.0
        breakdown["ranking"] = 0.0
        feedback.append("query.py missing.")

    print(json.dumps({"breakdown": breakdown, "feedback": feedback, "bonus_features": []}))

if __name__ == "__main__":
    main()
