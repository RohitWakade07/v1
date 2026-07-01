#!/usr/bin/env python3
"""
Week 6 Test Wrapper — runs inside the Docker sandbox.
Tests the student's analyze.py interactive CLI tool.
Output: one JSON object on stdout (parsed by Week6Grader).

Expected submission: analyze.py + (optionally) requirements.txt + README.md
Test data: test_data/ folder (injected as an asset) with file1.txt, file2.txt
"""
import json
import os
import subprocess
import sys
import time

SCRIPT = "analyze.py"
TEST_DATA_DIR = "test_data"
TIMEOUT = 10  # seconds per command session


def run_with_stdin(commands: list[str], timeout: int = TIMEOUT) -> tuple[int, str, str]:
    """Run analyze.py with piped stdin commands and capture output."""
    input_str = "\n".join(commands) + "\n"
    try:
        r = subprocess.run(
            [sys.executable, SCRIPT, TEST_DATA_DIR],
            input=input_str,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return 124, "", "TIMEOUT"
    except Exception as e:
        return 1, "", str(e)


def main():
    breakdown = {
        "repo_structure": 0.0,
        "stats_command":  0.0,
        "search_command": 0.0,
        "top_command":    0.0,
        "quit_command":   0.0,
        "error_handling": 0.0,
    }
    feedback: list[str] = []

    # ── A. Repository structure (30 pts) ────────────────────────────────
    pts_struct = 0.0

    # README.md (15 pts)
    readme_path = "README.md"
    if os.path.isfile(readme_path):
        readme_text = open(readme_path, encoding="utf-8", errors="ignore").read()
        word_count  = len(readme_text.split())
        if word_count >= 30:
            pts_struct += 15.0
            feedback.append(f"repo structure: README.md found with {word_count} words.")
        else:
            pts_struct += 7.0
            feedback.append(f"repo structure: README.md found but only {word_count} words (need ≥30).")
    else:
        feedback.append("repo structure: README.md not found.")

    # requirements.txt (10 pts)
    if os.path.isfile("requirements.txt"):
        pts_struct += 10.0
        feedback.append("repo structure: requirements.txt found.")
    else:
        feedback.append("repo structure: requirements.txt not found.")

    # analyze.py exists (5 pts)
    if os.path.isfile(SCRIPT):
        pts_struct += 5.0
        feedback.append("repo structure: analyze.py found.")
    else:
        feedback.append(f"repo structure: {SCRIPT} not found — cannot run any tests.")
        result = {
            "breakdown": {k: 0.0 for k in breakdown},
            "feedback":  feedback,
            "bonus_features": [],
        }
        result["breakdown"]["repo_structure"] = pts_struct
        print(json.dumps(result))
        return

    breakdown["repo_structure"] = pts_struct

    # ── B. stats command (20 pts) ────────────────────────────────────────
    rc, out, err = run_with_stdin(["stats file1.txt", "quit"])
    out_lower = out.lower()
    if rc == 124:
        feedback.append("stats command: TIMEOUT — program may be stuck waiting for input.")
    elif "lines" in out_lower and "words" in out_lower and "characters" in out_lower:
        breakdown["stats_command"] = 20.0
        feedback.append("stats command: correctly reports Lines, Words, and Characters.")
    elif "lines" in out_lower or "words" in out_lower:
        breakdown["stats_command"] = 10.0
        feedback.append("stats command: partial — only some stats printed.")
    else:
        feedback.append(f"stats command: output did not contain Lines/Words/Characters. Got: {out[:200]}")

    # ── C. search command (20 pts) ───────────────────────────────────────
    rc, out, err = run_with_stdin(["search python", "quit"])
    out_lower = out.lower()
    if rc == 124:
        feedback.append("search command: TIMEOUT.")
    elif "file1.txt" in out_lower or "file2.txt" in out_lower:
        breakdown["search_command"] = 20.0
        feedback.append("search command: correctly finds files containing the query word.")
    elif "not found" in out_lower or "no results" in out_lower:
        # Search ran but returned no results — the word might not be in test data
        breakdown["search_command"] = 10.0
        feedback.append("search command: ran but returned 'not found' — check case-insensitive matching.")
    else:
        feedback.append(f"search command: unexpected output. Got: {out[:200]}")

    # ── D. top command (10 pts) ──────────────────────────────────────────
    rc, out, err = run_with_stdin(["top 3 file1.txt", "quit"])
    out_lower = out.lower()
    if rc == 124:
        feedback.append("top command: TIMEOUT.")
    elif ":" in out and any(c.isdigit() for c in out):
        breakdown["top_command"] = 10.0
        feedback.append("top command: correctly shows top N words with counts.")
    elif out.strip():
        breakdown["top_command"] = 5.0
        feedback.append("top command: partial output — expected 'word: count' format.")
    else:
        feedback.append("top command: no output produced.")

    # ── E. quit command (10 pts) ─────────────────────────────────────────
    rc, out, err = run_with_stdin(["quit"])
    if rc == 0:
        breakdown["quit_command"] = 10.0
        feedback.append("quit command: program exits with code 0.")
    elif rc == 124:
        feedback.append("quit command: TIMEOUT — program did not respond to 'quit'.")
    else:
        feedback.append(f"quit command: exited with non-zero code {rc}.")

    # ── F. error handling (10 pts) ───────────────────────────────────────
    pts_err = 0.0

    # Unknown command
    rc, out, err = run_with_stdin(["foobarcommand", "quit"])
    if rc != 124 and out.strip():
        pts_err += 5.0
        feedback.append("error handling: handles unknown commands (prints error message).")
    else:
        feedback.append("error handling: does not handle unknown commands gracefully.")

    # stats with missing file
    rc, out, err = run_with_stdin(["stats nonexistent_file_xyz.txt", "quit"])
    if rc != 124 and ("error" in out.lower() or "not found" in out.lower() or out.strip()):
        pts_err += 5.0
        feedback.append("error handling: handles missing file gracefully.")
    else:
        feedback.append("error handling: does not handle missing file gracefully.")

    breakdown["error_handling"] = pts_err

    # ── Bonus feature detection ──────────────────────────────────────────
    bonus_keywords = {
        "fuzzywuzzy": "Fuzzy search",
        "rapidfuzz":  "Fuzzy search",
        "difflib":    "Fuzzy/diff search",
        "argparse":   "CLI argument parsing",
        "readline":   "Command history",
        "colorama":   "Colorized output",
        "rich":       "Rich terminal output",
        "tfidf":      "TF-IDF weighting",
    }
    bonus_features: list[str] = []
    try:
        src = open(SCRIPT, encoding="utf-8", errors="ignore").read().lower()
        for kw, desc in bonus_keywords.items():
            if kw in src:
                bonus_features.append(desc)
    except Exception:
        pass

    result = {
        "breakdown":     breakdown,
        "feedback":      feedback,
        "bonus_features": bonus_features,
    }
    print(json.dumps(result))


if __name__ == "__main__":
    main()
