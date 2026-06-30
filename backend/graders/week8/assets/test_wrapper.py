import os
import json
import subprocess
import sys
import glob

def grade():
    breakdown = {
        "modularity": 0,
        "execution": 0,
        "per_document_metadata": 0,
        "corpus_metadata": 0
    }
    feedback = []

    # 1. Modularity (30 pts)
    pkg_dir = "metadata_organizer"
    if os.path.isdir(pkg_dir):
        py_files = glob.glob(f"{pkg_dir}/*.py")
        if len(py_files) >= 3:
            breakdown["modularity"] = 30
            feedback.append("Modularity (30/30): Found at least 3 python modules in metadata_organizer.")
        else:
            breakdown["modularity"] = 15
            feedback.append(f"Modularity (15/30): Found {len(py_files)} python modules in metadata_organizer, expected at least 3.")
    else:
        feedback.append("Modularity (0/30): Package directory 'metadata_organizer' not found.")

    # 2. Execution (20 pts)
    try:
        proc = subprocess.run([sys.executable, "main.py"], capture_output=True, text=True, timeout=10)
        if proc.returncode == 0:
            breakdown["execution"] = 20
            feedback.append("Execution (20/20): main.py executed successfully.")
        else:
            feedback.append(f"Execution (0/20): Script exited with {proc.returncode}. {proc.stderr[:200]}")
    except Exception as e:
        feedback.append(f"Execution (0/20): Failed to execute: {e}")

    # 3. Output Validation (50 pts)
    if os.path.exists("metadata.json"):
        try:
            with open("metadata.json", "r") as f:
                data = json.load(f)
            
            # Per-doc metadata (25 pts)
            # Support both 'documents' and 'articles' array names
            docs = data.get("documents", data.get("articles", []))
            
            # If the student placed per-doc metadata at the root (not in a list), try extracting it
            if not docs and all(isinstance(v, dict) for k, v in data.items() if k not in ["total_documents", "average_length", "vocabulary_size"]):
                docs = [v for k, v in data.items() if isinstance(v, dict)]

            if isinstance(docs, list) and len(docs) > 0:
                doc = docs[0]
                expected_keys = {"title", "url", "word_count", "unique_word_count", "top_terms"}
                
                # Check for case insensitivity or slight variations (e.g. top_10_terms)
                doc_keys_lower = set(k.lower() for k in doc.keys())
                has_all = True
                for ek in expected_keys:
                    if not any(ek in dk for dk in doc_keys_lower):
                        has_all = False
                
                if has_all:
                    breakdown["per_document_metadata"] = 25
                    feedback.append("Per-Document Metadata (25/25): Correct schema for document metadata.")
                else:
                    feedback.append(f"Per-Document Metadata (0/25): Missing expected fields. Found {list(doc.keys())}")
            else:
                feedback.append("Per-Document Metadata (0/25): No valid document metadata records found in metadata.json.")

            # Corpus metadata (25 pts)
            corpus_keys = {"total_documents", "average_length", "vocabulary_size"}
            data_keys_lower = set(k.lower() for k in data.keys())
            has_corpus_keys = all(any(ck in dk for dk in data_keys_lower) for ck in corpus_keys)
            
            if has_corpus_keys:
                breakdown["corpus_metadata"] = 25
                feedback.append("Corpus Metadata (25/25): Correct schema for corpus-level metadata.")
            else:
                feedback.append(f"Corpus Metadata (0/25): Missing expected keys (total_documents, average_length, vocabulary_size).")
        except Exception as e:
            feedback.append(f"Output Validation (0/50): Failed to parse metadata.json - {e}")
    else:
        feedback.append("Output Validation (0/50): metadata.json not found.")

    print(json.dumps({"breakdown": breakdown, "feedback": feedback}))

if __name__ == "__main__":
    grade()
