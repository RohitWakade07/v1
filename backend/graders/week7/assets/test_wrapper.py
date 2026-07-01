#!/usr/bin/env python3
"""
Week 7 Test Wrapper — Web Scraper (collect_wiki.py)
Runs inside Docker sandbox. Tests the student's web scraper.
Output: JSON with breakdown + feedback.

Scoring:
  execution        : 20 pts — script runs without crash
  corpus_dir       : 20 pts — corpus/ directory created with ≥ 3 JSON files
  json_schema      : 30 pts — each JSON file has title, url, text keys
  content_quality  : 30 pts — text content is non-trivial (≥ 50 words)
"""
import json
import os
import subprocess
import sys
import time

SCRIPT = "collect_wiki.py"
CORPUS_DIR = "corpus"
TIMEOUT = 60  # web scraping may be slow

REQUIRED_KEYS = {"title", "url", "text"}
MIN_WORDS_PER_DOC = 50
MIN_DOCS = 3


def main():
    breakdown = {
        "execution":       0.0,
        "corpus_dir":      0.0,
        "json_schema":     0.0,
        "content_quality": 0.0,
    }
    feedback: list[str] = []

    # ── A. Repo structure ────────────────────────────────────────────────
    readme_ok = os.path.isfile("README.md")
    reqs_ok   = os.path.isfile("requirements.txt")
    script_ok = os.path.isfile(SCRIPT)

    if readme_ok:
        feedback.append("Repository structure: README.md found.")
    else:
        feedback.append("Repository structure: README.md missing.")
    if reqs_ok:
        feedback.append("Repository structure: requirements.txt found.")
    else:
        feedback.append("Repository structure: requirements.txt missing.")

    if not script_ok:
        feedback.append(f"Execution: {SCRIPT} not found — cannot run tests.")
        result = {"breakdown": breakdown, "feedback": feedback, "bonus_features": []}
        print(json.dumps(result))
        return

    # ── B. Execution (20 pts) ────────────────────────────────────────────
    try:
        r = subprocess.run(
            [sys.executable, SCRIPT],
            capture_output=True, text=True, timeout=TIMEOUT,
        )
        exit_code = r.returncode
    except subprocess.TimeoutExpired:
        exit_code = 124
    except Exception as e:
        exit_code = 1
        feedback.append(f"Execution: exception — {e}")

    if exit_code == 0:
        breakdown["execution"] = 20.0
        feedback.append("Execution: collect_wiki.py ran successfully (exit 0).")
    elif exit_code == 124:
        feedback.append("Execution: TIMEOUT — script took > 60 seconds.")
    else:
        feedback.append(f"Execution: script exited with code {exit_code}.")

    # ── C. Corpus directory (20 pts) ─────────────────────────────────────
    json_files: list[str] = []
    if os.path.isdir(CORPUS_DIR):
        json_files = [
            f for f in os.listdir(CORPUS_DIR)
            if f.endswith(".json")
        ]
        doc_count = len(json_files)
        if doc_count >= MIN_DOCS:
            breakdown["corpus_dir"] = 20.0
            feedback.append(f"Corpus directory: {doc_count} JSON files found in corpus/.")
        elif doc_count > 0:
            breakdown["corpus_dir"] = round(doc_count / MIN_DOCS * 20.0, 1)
            feedback.append(f"Corpus directory: only {doc_count}/{MIN_DOCS} JSON files found.")
        else:
            feedback.append("Corpus directory: corpus/ exists but contains no JSON files.")
    else:
        feedback.append("Corpus directory: corpus/ directory not found.")

    if not json_files:
        result = {"breakdown": breakdown, "feedback": feedback, "bonus_features": []}
        print(json.dumps(result))
        return

    # ── D. JSON schema validation (30 pts) ───────────────────────────────
    schema_pass = 0
    for fname in json_files[:10]:  # check up to 10 files
        path = os.path.join(CORPUS_DIR, fname)
        try:
            with open(path, encoding="utf-8") as f:
                doc = json.load(f)
            if REQUIRED_KEYS.issubset(doc.keys()):
                schema_pass += 1
        except Exception:
            pass

    schema_ratio = schema_pass / min(len(json_files), 10)
    breakdown["json_schema"] = round(schema_ratio * 30.0, 1)
    feedback.append(
        f"JSON schema: {schema_pass}/{min(len(json_files),10)} files have title, url, text keys."
    )

    # ── E. Content quality (30 pts) ──────────────────────────────────────
    quality_pass = 0
    for fname in json_files[:10]:
        path = os.path.join(CORPUS_DIR, fname)
        try:
            with open(path, encoding="utf-8") as f:
                doc = json.load(f)
            text  = doc.get("text", "")
            title = doc.get("title", "")
            if len(text.split()) >= MIN_WORDS_PER_DOC and len(title) > 2:
                quality_pass += 1
        except Exception:
            pass

    quality_ratio = quality_pass / min(len(json_files), 10)
    breakdown["content_quality"] = round(quality_ratio * 30.0, 1)
    feedback.append(
        f"Content quality: {quality_pass}/{min(len(json_files),10)} files have ≥{MIN_WORDS_PER_DOC} words."
    )

    # ── Bonus features ───────────────────────────────────────────────────
    bonus_keywords = {
        "beautifulsoup": "BeautifulSoup HTML parsing",
        "lxml":          "LXML fast parser",
        "selenium":      "Selenium dynamic scraping",
        "playwright":    "Playwright browser automation",
        "rate_limit":    "Rate limiting / polite scraping",
        "time.sleep":    "Polite delay between requests",
        "retry":         "Retry logic for failed requests",
        "robots":        "robots.txt compliance",
    }
    bonus_features: list[str] = []
    try:
        src = open(SCRIPT, encoding="utf-8", errors="ignore").read().lower()
        for kw, desc in bonus_keywords.items():
            if kw in src:
                bonus_features.append(desc)
    except Exception:
        pass

    result = {"breakdown": breakdown, "feedback": feedback, "bonus_features": bonus_features}
    print(json.dumps(result))


if __name__ == "__main__":
    main()
