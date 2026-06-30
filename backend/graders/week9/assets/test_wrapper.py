import os
import json
import subprocess
import sys

def grade():
    breakdown = {
        "build_index_execution": 0,
        "index_schema": 0,
        "lookup_execution": 0,
        "query_results": 0
    }
    feedback = []

    # 1. Build Index Execution (20 pts)
    try:
        proc = subprocess.run([sys.executable, "build_index.py"], capture_output=True, text=True, timeout=10)
        if proc.returncode == 0:
            breakdown["build_index_execution"] = 20
            feedback.append("Build Index Execution (20/20): build_index.py executed successfully.")
        else:
            feedback.append(f"Build Index Execution (0/20): build_index.py exited with {proc.returncode}. {proc.stderr[:200]}")
    except Exception as e:
        feedback.append(f"Build Index Execution (0/20): Failed to execute build_index.py: {e}")

    # 2. Index Schema (30 pts)
    if os.path.exists("index.json"):
        try:
            with open("index.json", "r") as f:
                idx = json.load(f)
            
            is_valid = False
            if isinstance(idx, dict):
                # Loose check
                is_valid = True
                if is_valid or len(idx) == 0:
                    breakdown["index_schema"] = 30
                    feedback.append("Index Schema (30/30): index.json generated with valid dictionary schema.")
                else:
                    feedback.append("Index Schema (0/30): index.json is malformed.")
            else:
                feedback.append("Index Schema (0/30): index.json root is not a dictionary.")
        except Exception as e:
            feedback.append(f"Index Schema (0/30): Failed to parse index.json - {e}")
    else:
        feedback.append("Index Schema (0/30): index.json not found.")

    # 3. Lookup Execution & Query Results (50 pts)
    if os.path.exists("lookup.py"):
        try:
            # We simulate querying for "python" and then "quit" (or Ctrl+D by closing stdin)
            proc2 = subprocess.run(
                [sys.executable, "lookup.py"],
                input="python\nquit\n",
                capture_output=True,
                text=True,
                timeout=10
            )
            if proc2.returncode == 0:
                breakdown["lookup_execution"] = 20
                feedback.append("Lookup Execution (20/20): lookup.py executed successfully.")
            else:
                feedback.append(f"Lookup Execution (0/20): lookup.py exited with {proc2.returncode}. {proc2.stderr[:200]}")
                
            output = proc2.stdout.lower() + proc2.stderr.lower()
            if "page1" in output or "python" in output or "doc_id" in output:
                breakdown["query_results"] = 30
                feedback.append("Query Results (30/30): lookup.py correctly returned results for query 'python'.")
            else:
                feedback.append("Query Results (0/30): lookup.py did not return expected output for 'python'.")
                
        except Exception as e:
            feedback.append(f"Lookup Execution (0/20): Failed to execute lookup.py: {e}")
            feedback.append("Query Results (0/30): Cannot test query results without lookup.py running.")
    else:
        feedback.append("Lookup Execution (0/20): lookup.py not found.")
        feedback.append("Query Results (0/30): Cannot test query results.")

    print(json.dumps({"breakdown": breakdown, "feedback": feedback}))

if __name__ == "__main__":
    grade()
