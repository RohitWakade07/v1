#!/usr/bin/env python3
"""
Week 12 – Capstone Test Wrapper
Runs automated checks on the student's Semantic Search Engine submission.
Outputs a JSON report that the grader parses.
"""
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
    bonus_features = []

    # ── 1. Engineering Quality (20 pts) ──────────────────────────────
    eq_pts = 0.0
    if os.path.isfile("README.md"):
        readme_size = os.path.getsize("README.md")
        if readme_size > 200:
            eq_pts += 10.0
            feedback.append("README.md found with meaningful content.")
        else:
            eq_pts += 5.0
            feedback.append("README.md found but very short.")
    else:
        feedback.append("README.md missing — include project documentation.")

    # Check for modular code structure
    py_files = [f for f in os.listdir(".") if f.endswith(".py")]
    if len(py_files) >= 3:
        eq_pts += 5.0
        feedback.append(f"Good modular structure: {len(py_files)} Python files found.")
    else:
        feedback.append(f"Only {len(py_files)} Python file(s) found — consider modular design.")

    # Check for requirements.txt
    if os.path.isfile("requirements.txt"):
        eq_pts += 5.0
        feedback.append("requirements.txt found.")
    else:
        feedback.append("requirements.txt missing — include project dependencies.")

    breakdown["engineering_quality"] = min(eq_pts, 20.0)

    # ── 2. Dataset (10 pts) ──────────────────────────────────────────
    corpus_dir = None
    for candidate in ["corpus", "data", "documents", "dataset"]:
        if os.path.isdir(candidate):
            corpus_dir = candidate
            break

    if corpus_dir:
        corpus_files = [f for f in os.listdir(corpus_dir) if f.endswith(".json")]
        if len(corpus_files) >= 50:
            breakdown["dataset"] = 10.0
            feedback.append(f"Dataset contains {len(corpus_files)} JSON documents (≥50 required).")
        elif len(corpus_files) >= 10:
            breakdown["dataset"] = 7.0
            feedback.append(f"Dataset has {len(corpus_files)} documents — needs ≥50 for full marks.")
        elif len(corpus_files) >= 3:
            breakdown["dataset"] = 5.0
            feedback.append(f"Dataset has only {len(corpus_files)} documents — too small.")
        else:
            breakdown["dataset"] = 2.0
            feedback.append(f"Dataset has only {len(corpus_files)} JSON files.")

        # Validate JSON structure
        valid_docs = 0
        for cf in corpus_files[:5]:  # sample check
            try:
                with open(os.path.join(corpus_dir, cf)) as fh:
                    doc = json.load(fh)
                    if "content" in doc and len(doc["content"]) > 10:
                        valid_docs += 1
            except Exception:
                pass
        if valid_docs == 0 and len(corpus_files) > 0:
            breakdown["dataset"] = max(breakdown["dataset"] - 3.0, 0.0)
            feedback.append("Warning: JSON documents do not appear to have meaningful 'content' fields.")
    else:
        breakdown["dataset"] = 0.0
        feedback.append("No corpus/ or data/ directory found.")

    # ── 3. Persistent Inverted Index (20 pts) ────────────────────────
    if os.path.isfile("build_index.py"):
        try:
            result = subprocess.run(
                [sys.executable, "build_index.py"],
                capture_output=True, timeout=TIMEOUT, text=True
            )
            # Check if index was created
            index_file = None
            for candidate in ["index.json", "index.pkl", "index.pickle", "index.db", "index.dat"]:
                if os.path.isfile(candidate):
                    index_file = candidate
                    break

            if index_file:
                idx_size = os.path.getsize(index_file)
                if idx_size > 100:
                    breakdown["persistent_inverted_index"] = 20.0
                    feedback.append(f"build_index.py created {index_file} ({idx_size} bytes).")
                else:
                    breakdown["persistent_inverted_index"] = 10.0
                    feedback.append(f"{index_file} was created but seems too small ({idx_size} bytes).")
            else:
                breakdown["persistent_inverted_index"] = 5.0
                feedback.append("build_index.py ran but no index file was created (expected index.json/pkl/db).")

            if result.returncode != 0:
                feedback.append(f"build_index.py exited with code {result.returncode}: {result.stderr[:200]}")
        except subprocess.TimeoutExpired:
            breakdown["persistent_inverted_index"] = 0.0
            feedback.append(f"build_index.py timed out after {TIMEOUT}s.")
        except Exception as e:
            breakdown["persistent_inverted_index"] = 0.0
            feedback.append(f"build_index.py error: {str(e)[:200]}")
    else:
        breakdown["persistent_inverted_index"] = 0.0
        feedback.append("build_index.py not found.")

    # ── 4 & 5. Query Handling (35 pts) + Ranking (15 pts) ────────────
    query_script = None
    for candidate in ["query.py", "search.py", "main.py"]:
        if os.path.isfile(candidate):
            query_script = candidate
            break

    if query_script:
        try:
            import pexpect
        except ImportError:
            subprocess.run([sys.executable, "-m", "pip", "install", "pexpect"],
                          capture_output=True, timeout=30)
            import pexpect

        # Anti-cheat: test with a nonsense query first
        try:
            child = pexpect.spawn(sys.executable, [query_script], timeout=10, encoding="utf-8")
            child.sendline("xyzzy_nonsense_query_12345")
            child.expect([pexpect.TIMEOUT, pexpect.EOF], timeout=3)
            spoof_output = (child.before or "").lower()
            if child.isalive():
                child.sendline("quit")
            child.close()

            # If a real doc name appears for a nonsense query, they're faking it
            if corpus_dir:
                corpus_file_names = [f.replace(".json", "").lower() for f in os.listdir(corpus_dir) if f.endswith(".json")]
            else:
                corpus_file_names = []

            spoofed = False
            for doc_name in corpus_file_names:
                if doc_name and doc_name != "doc" and doc_name in spoof_output:
                    spoofed = True
                    break

            if spoofed:
                breakdown["query_handling"] = 0.0
                breakdown["ranking"] = 0.0
                feedback.append(f"{query_script} returned documents for a nonsense query — possible hardcoding detected.")
                print(json.dumps({"breakdown": breakdown, "feedback": feedback, "bonus_features": bonus_features}))
                return
        except Exception:
            pass

        # Actual query test
        try:
            child = pexpect.spawn(sys.executable, [query_script], timeout=10, encoding="utf-8")

            # Test query 1: should find relevant results
            child.sendline("python programming language")
            child.expect([pexpect.TIMEOUT, pexpect.EOF], timeout=5)
            q1_output = (child.before or "").lower()

            # Test query 2: a second consecutive query (tests loop handling)
            q2_output = ""
            if child.isalive():
                child.sendline("database SQL")
                child.expect([pexpect.TIMEOUT, pexpect.EOF], timeout=5)
                q2_output = (child.before or "").lower()

            if child.isalive():
                child.sendline("quit")
                try:
                    child.expect(pexpect.EOF, timeout=3)
                except Exception:
                    pass
            child.close()

            combined = q1_output + q2_output

            # Check if any meaningful output was produced
            has_results = (
                "doc" in combined or
                "result" in combined or
                "found" in combined or
                "title" in combined or
                "score" in combined or
                "rank" in combined or
                "python" in combined or
                "database" in combined
            )

            if has_results and q2_output:
                breakdown["query_handling"] = 35.0
                breakdown["ranking"] = 15.0
                feedback.append(f"{query_script} handled multiple queries correctly and returned results.")
            elif has_results:
                breakdown["query_handling"] = 25.0
                breakdown["ranking"] = 10.0
                feedback.append(f"{query_script} handled a single query but did not support consecutive queries.")
            else:
                breakdown["query_handling"] = 5.0
                breakdown["ranking"] = 0.0
                feedback.append(f"{query_script} ran but did not return meaningful search results.")

        except pexpect.exceptions.EOF:
            breakdown["query_handling"] = 5.0
            breakdown["ranking"] = 0.0
            feedback.append(f"{query_script} exited unexpectedly (EOF).")
        except pexpect.exceptions.TIMEOUT:
            breakdown["query_handling"] = 5.0
            breakdown["ranking"] = 0.0
            feedback.append(f"{query_script} timed out waiting for output.")
        except Exception as e:
            breakdown["query_handling"] = 0.0
            breakdown["ranking"] = 0.0
            feedback.append(f"{query_script} exception: {str(e)[:200]}")
    else:
        breakdown["query_handling"] = 0.0
        breakdown["ranking"] = 0.0
        feedback.append("No query script found (expected query.py, search.py, or main.py).")

    # ── Bonus checks ─────────────────────────────────────────────────
    if os.path.isfile("engine/__init__.py") or os.path.isfile("search_engine/__init__.py"):
        bonus_features.append("Modular package structure")
    if any("tfidf" in f.lower() or "tf_idf" in f.lower() for f in py_files):
        bonus_features.append("Dedicated TF-IDF module")
    if os.path.isfile(".gitignore"):
        bonus_features.append(".gitignore present")

    print(json.dumps({"breakdown": breakdown, "feedback": feedback, "bonus_features": bonus_features}))


if __name__ == "__main__":
    main()
