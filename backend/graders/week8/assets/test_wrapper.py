#!/usr/bin/env python3
"""
Week 8 Test Wrapper — Metadata Organizer / NLP Basics
Runs inside Docker sandbox. Tests main.py and the metadata_organizer package.

Scoring (100 pts):
  modularity           : 30 pts — package structure (loader, tokenizer, writer modules)
  execution            : 20 pts — main.py runs and exits 0
  per_document_metadata: 25 pts — each doc has title, url, word_count, unique_word_count, top_10_terms
  corpus_metadata      : 25 pts — output has total_documents, average_length, vocabulary_size
"""
import json
import os
import subprocess
import sys

SCRIPT  = "main.py"
CORPUS  = "corpus"  # injected by grader assets
OUTPUT  = "metadata.json"
TIMEOUT = 30


def main():
    breakdown = {
        "modularity":            0.0,
        "execution":             0.0,
        "per_document_metadata": 0.0,
        "corpus_metadata":       0.0,
    }
    feedback: list[str] = []

    # ── A. Modularity (30 pts) ───────────────────────────────────────────
    pts_mod = 0.0
    pkg = "metadata_organizer"
    if os.path.isdir(pkg):
        pts_mod += 10.0
        feedback.append(f"Modularity: {pkg}/ package directory found.")
        modules = {"loader": 8.0, "tokenizer": 7.0, "writer": 5.0}
        for mod, pts in modules.items():
            fpath = os.path.join(pkg, f"{mod}.py")
            if os.path.isfile(fpath):
                pts_mod += pts
                feedback.append(f"Modularity: {pkg}/{mod}.py found.")
            else:
                feedback.append(f"Modularity: {pkg}/{mod}.py missing.")
    else:
        feedback.append(f"Modularity: {pkg}/ package not found.")

    # Bonus: __init__.py
    if os.path.isfile(os.path.join(pkg, "__init__.py")):
        feedback.append(f"Modularity: {pkg}/__init__.py found.")

    breakdown["modularity"] = min(pts_mod, 30.0)

    # ── B. Execution (20 pts) ────────────────────────────────────────────
    if not os.path.isfile(SCRIPT):
        feedback.append("Execution: main.py not found.")
        print(json.dumps({"breakdown": breakdown, "feedback": feedback, "bonus_features": []}))
        return

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
        feedback.append("Execution: main.py ran successfully (exit 0).")
    elif exit_code == 124:
        feedback.append("Execution: TIMEOUT (>30s).")
    else:
        feedback.append(f"Execution: exited with code {exit_code}. Stderr: {r.stderr[:200]}")

    # ── C & D. metadata.json validation ─────────────────────────────────
    if not os.path.isfile(OUTPUT):
        feedback.append(f"Output: {OUTPUT} not created.")
        print(json.dumps({"breakdown": breakdown, "feedback": feedback, "bonus_features": []}))
        return

    try:
        with open(OUTPUT, encoding="utf-8") as f:
            meta = json.load(f)
    except Exception as e:
        feedback.append(f"Output: {OUTPUT} is not valid JSON — {e}")
        print(json.dumps({"breakdown": breakdown, "feedback": feedback, "bonus_features": []}))
        return

    # ── C. Corpus-level metadata (25 pts) ────────────────────────────────
    pts_corpus = 0.0
    required_corpus = {
        "total_documents":  10.0,
        "average_length":   8.0,
        "vocabulary_size":  7.0,
    }
    for key, pts in required_corpus.items():
        # Accept various key formats: snake_case, "total documents", etc.
        matched = any(
            key.replace("_", "") in k.replace(" ", "").lower()
            or key.replace("_", " ") == k.lower()
            or key == k
            for k in meta.keys()
        )
        if matched:
            pts_corpus += pts
            feedback.append(f"Corpus metadata: '{key}' found in metadata.json.")
        else:
            feedback.append(f"Corpus metadata: '{key}' missing from metadata.json.")
    breakdown["corpus_metadata"] = min(pts_corpus, 25.0)

    # ── D. Per-document metadata (25 pts) ────────────────────────────────
    docs_list = None
    for key in meta.keys():
        if "document" in key.lower() and isinstance(meta[key], list):
            docs_list = meta[key]
            break

    if not docs_list:
        feedback.append("Per-document metadata: 'documents' list not found in metadata.json.")
    else:
        doc_fields = {"title", "url", "word_count", "unique_word_count", "top_10_terms"}
        all_ok = 0
        for doc in docs_list[:5]:
            # Flexible key matching
            doc_keys_norm = {k.replace(" ", "_").lower() for k in doc.keys()}
            matched_fields = sum(
                1 for f in doc_fields
                if f in doc_keys_norm or f.replace("_", " ") in doc.keys()
                or f in doc.keys()
            )
            if matched_fields >= 4:
                all_ok += 1

        ratio = all_ok / max(len(docs_list[:5]), 1)
        pts_doc = round(ratio * 25.0, 1)
        breakdown["per_document_metadata"] = pts_doc
        feedback.append(
            f"Per-document metadata: {all_ok}/{min(len(docs_list),5)} docs have ≥4/5 required fields."
        )

    # ── Bonus features ───────────────────────────────────────────────────
    bonus_keywords = {"nltk": "NLTK", "spacy": "spaCy", "stemm": "Stemming", "lemmat": "Lemmatization"}
    bonus_features: list[str] = []
    py_files = [SCRIPT] + [
        os.path.join(pkg, f) for f in os.listdir(pkg) if f.endswith(".py")
    ] if os.path.isdir(pkg) else [SCRIPT]
    for fpath in py_files:
        try:
            src = open(fpath, errors="ignore").read().lower()
            for kw, desc in bonus_keywords.items():
                if kw in src and desc not in bonus_features:
                    bonus_features.append(desc)
        except Exception:
            pass

    print(json.dumps({"breakdown": breakdown, "feedback": feedback, "bonus_features": bonus_features}))


if __name__ == "__main__":
    main()
