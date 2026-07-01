#!/usr/bin/env python3
"""
Week 9 Test Wrapper — Search Engine (Inverted Index)
Runs inside Docker sandbox. Tests build_index.py and lookup.py.

Scoring (100 pts):
  build_index_execution : 20 pts — build_index.py runs and creates index.json
  index_schema          : 30 pts — index.json structure is valid
  lookup_execution      : 20 pts — lookup.py runs with provided input
  query_results         : 30 pts — lookup.py returns correct results for a query
"""
import json
import os
import subprocess
import sys

BUILD_SCRIPT = "build_index.py"
LOOKUP_SCRIPT = "lookup.py"
CORPUS = "corpus"
INDEX = "index.json"
TIMEOUT = 30


def main():
    breakdown = {
        "build_index_execution": 0.0,
        "index_schema":          0.0,
        "lookup_execution":      0.0,
        "query_results":         0.0,
    }
    feedback = []

    # ── 1. Repo Structure ───────────────────────────────────────────────
    if not os.path.isfile(BUILD_SCRIPT):
        feedback.append(f"{BUILD_SCRIPT} missing.")
    if not os.path.isfile(LOOKUP_SCRIPT):
        feedback.append(f"{LOOKUP_SCRIPT} missing.")
    
    if not os.path.isfile(BUILD_SCRIPT):
        print(json.dumps({"breakdown": breakdown, "feedback": feedback, "bonus_features": []}))
        return

    # ── 2. Build Index Execution (20 pts) ───────────────────────────────
    try:
        r_build = subprocess.run(
            [sys.executable, BUILD_SCRIPT],
            capture_output=True, text=True, timeout=TIMEOUT,
        )
        if r_build.returncode == 0:
            if os.path.isfile(INDEX):
                breakdown["build_index_execution"] = 20.0
                feedback.append(f"{BUILD_SCRIPT} ran and created {INDEX}.")
            else:
                breakdown["build_index_execution"] = 10.0
                feedback.append(f"{BUILD_SCRIPT} ran successfully but {INDEX} was not created.")
        else:
            feedback.append(f"{BUILD_SCRIPT} failed with exit code {r_build.returncode}.")
    except subprocess.TimeoutExpired:
        feedback.append(f"{BUILD_SCRIPT} timed out.")
    except Exception as e:
        feedback.append(f"{BUILD_SCRIPT} exception: {e}")

    # ── 3. Index Schema (30 pts) ────────────────────────────────────────
    if os.path.isfile(INDEX):
        try:
            with open(INDEX, encoding="utf-8") as f:
                index_data = json.load(f)
            
            if isinstance(index_data, dict) and len(index_data) > 0:
                sample_term = list(index_data.keys())[0]
                if isinstance(index_data[sample_term], dict):
                    breakdown["index_schema"] = 30.0
                    feedback.append(f"{INDEX} has valid schema (term -> doc -> freq).")
                else:
                    breakdown["index_schema"] = 15.0
                    feedback.append(f"{INDEX} structure partial (term not mapping to dict of docs).")
            else:
                feedback.append(f"{INDEX} is empty or not a dict.")
        except Exception as e:
            feedback.append(f"{INDEX} is not valid JSON: {e}")
    else:
        feedback.append(f"Cannot validate schema, {INDEX} missing.")

    # ── 4. Lookup Execution & Results (50 pts total) ─────────────────────
    if not os.path.isfile(LOOKUP_SCRIPT):
        print(json.dumps({"breakdown": breakdown, "feedback": feedback, "bonus_features": []}))
        return

    # We provide a known word as input to lookup.py
    # If using standard corpus, 'the' or 'python' is usually present. Let's use 'python'.
    query = "python"
    try:
        r_lookup = subprocess.run(
            [sys.executable, LOOKUP_SCRIPT],
            input=f"{query}\n",
            capture_output=True, text=True, timeout=TIMEOUT,
        )
        if r_lookup.returncode == 0:
            breakdown["lookup_execution"] = 20.0
            feedback.append(f"{LOOKUP_SCRIPT} ran successfully.")
            
            # Very basic check for query results. It should print document names.
            out_lower = r_lookup.stdout.lower()
            if "doc" in out_lower or ".json" in out_lower:
                breakdown["query_results"] = 30.0
                feedback.append(f"{LOOKUP_SCRIPT} returned plausible results for query '{query}'.")
            elif "not found" in out_lower or "no result" in out_lower:
                breakdown["query_results"] = 15.0
                feedback.append(f"{LOOKUP_SCRIPT} returned 'not found' for query '{query}'.")
            else:
                feedback.append(f"{LOOKUP_SCRIPT} output did not contain expected document identifiers.")
        else:
            feedback.append(f"{LOOKUP_SCRIPT} failed with exit code {r_lookup.returncode}.")
    except subprocess.TimeoutExpired:
        feedback.append(f"{LOOKUP_SCRIPT} timed out.")
    except Exception as e:
        feedback.append(f"{LOOKUP_SCRIPT} exception: {e}")

    # ── Bonus features ───────────────────────────────────────────────────
    bonus_keywords = {"tfidf": "TF-IDF implemented", "bm25": "BM25 implemented", "pickle": "Used pickle for fast loading"}
    bonus_features = []
    for script in [BUILD_SCRIPT, LOOKUP_SCRIPT]:
        if os.path.isfile(script):
            try:
                src = open(script, errors="ignore").read().lower()
                for kw, desc in bonus_keywords.items():
                    if kw in src and desc not in bonus_features:
                        bonus_features.append(desc)
            except Exception:
                pass

    print(json.dumps({"breakdown": breakdown, "feedback": feedback, "bonus_features": bonus_features}))


if __name__ == "__main__":
    main()
