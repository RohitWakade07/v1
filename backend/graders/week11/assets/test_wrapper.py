import json
import os
import sys
import subprocess

import time
import shutil

def grade():
    breakdown = {"engineering": 0, "corpus_size": 0, "multi_word": 0, "ranked": 0}
    feedback_messages = []
    REPO_DIR = os.getcwd()

    # 1. Structure & Engineering
    has_readme = os.path.exists("README.md")
    has_reqs = os.path.exists("requirements.txt")
    entrypoints = ["query.py", "engine.py", "main.py"]
    found_entrypoint = next((ep for ep in entrypoints if os.path.exists(ep)), None)
    
    is_modular = False
    for item in os.listdir(REPO_DIR):
        item_path = os.path.join(REPO_DIR, item)
        if os.path.isdir(item_path) and not item.startswith('.') and item != "corpus":
            if os.path.exists(os.path.join(item_path, "__init__.py")) or len([f for f in os.listdir(item_path) if f.endswith(".py")]) > 0:
                is_modular = True
                break

    if has_readme and has_reqs and found_entrypoint and is_modular:
        breakdown["engineering"] = 20
        feedback_messages.append("Engineering Quality (20/20): README, requirements.txt, entrypoint, and modular package structure detected.")
    else:
        feedback_messages.append(f"Engineering Quality (0/20): Missing structure. README: {has_readme}, Reqs: {has_reqs}, Entrypoint: {found_entrypoint}, Modular: {is_modular}")
        if not found_entrypoint:
            print(json.dumps({"breakdown": breakdown, "feedback": feedback_messages}))
            return

    # 2. Corpus Validation
    student_corpus = os.path.join(REPO_DIR, "corpus")
    if os.path.exists(student_corpus):
        json_count = len([f for f in os.listdir(student_corpus) if f.endswith(".json")])
        if json_count >= 50:
            breakdown["corpus_size"] = 10
            feedback_messages.append(f"Corpus Validation (10/10): Found {json_count} JSON articles in the corpus.")
        else:
            feedback_messages.append(f"Corpus Validation (0/10): Corpus only contains {json_count} articles. Minimum 50 required.")
    else:
        feedback_messages.append("Corpus Validation (0/10): No 'corpus' directory found.")

    # Dependencies
    if has_reqs:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], cwd=REPO_DIR)
        
    # Inject Mock Corpus for Testing
    instructor_corpus = os.path.join(REPO_DIR, "..", "test_corpus") # It gets mounted from assets/test_corpus usually, but let's just assume it's next to test_wrapper.py
    # Wait, the config.yaml maps 'test_corpus' to 'test_corpus' in the CWD of grader.
    instructor_corpus = "test_corpus"
    if os.path.exists(instructor_corpus):
        if os.path.exists(student_corpus):
            shutil.rmtree(student_corpus)
        shutil.copytree(instructor_corpus, student_corpus)

    # Build index if they have script
    has_build = os.path.exists("build_index.py")
    if has_build:
        try:
            subprocess.run([sys.executable, "build_index.py"], cwd=REPO_DIR, timeout=30)
        except Exception:
            pass
            
    if not os.path.exists("index.json"):
        with open("index.json", "w") as f:
            f.write('{"python": {"doc1": 1}, "mock": {"doc5": 1}, "article": {"doc5": 1}}')
    
    # Query Tests
    try:
        process = subprocess.run(
            [sys.executable, found_entrypoint], 
            cwd=REPO_DIR, 
            input="mock article\npython\n", 
            capture_output=True, 
            text=True, 
            timeout=5
        )
        output = process.stdout + process.stderr
        
        # Test 1: Multi-word query
        if "doc5" in output.lower() or "mock" in output.lower():
            breakdown["multi_word"] = 35
            feedback_messages.append("Multi-Word Query (35/35): Successfully handled a multi-word query.")
        else:
            feedback_messages.append(f"Multi-Word Query (10/35): Did not return expected results for 'mock article'. Output: {output.strip()[:100]}")
            
        # Test 2: Ranked Retrieval
        if "doc1" in output.lower() or "python" in output.lower():
            breakdown["ranked"] = 35
            feedback_messages.append("Ranked Retrieval (35/35): Successfully retrieved top documents for term 'python'.")
        else:
            feedback_messages.append(f"Ranked Retrieval (10/35): Did not return expected results for 'python'. Output: {output.strip()[:100]}")
            
    except Exception as e:
        feedback_messages.append(f"Query Testing (0/70): Failed to execute interactive query: {e}")

    print(json.dumps({"breakdown": breakdown, "feedback": feedback_messages}))

if __name__ == "__main__":
    grade()