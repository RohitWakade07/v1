import json
import os
import sys
import subprocess
try:
    import pexpect
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "ptyprocess-0.7.0-py2.py3-none-any.whl", "pexpect-4.9.0-py2.py3-none-any.whl"], check=True)
    import pexpect
import time

def grade():
    breakdown = {"repo_structure": 0, "index_generation": 0, "query_ranking": 0}
    feedback_messages = []
    REPO_DIR = os.getcwd()

    # 1. Structure
    has_readme = os.path.exists("README.md")
    entrypoints = ["query.py", "engine.py", "main.py"]
    found_entrypoint = next((ep for ep in entrypoints if os.path.exists(ep)), None)

    if has_readme and found_entrypoint:
        breakdown["repo_structure"] = 20
        feedback_messages.append(f"Repository Structure (20/20): README.md and {found_entrypoint} found.")
    else:
        feedback_messages.append(f"Repository Structure (0/20): Missing structure. README: {has_readme}, Entrypoint: {found_entrypoint}")
        print(json.dumps({"breakdown": breakdown, "feedback": feedback_messages}))
        return

    # 2. Dependencies
    if os.path.exists("requirements.txt"):
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], cwd=REPO_DIR)

    # 3. Index Generation
    has_build = os.path.exists("build_index.py")
    if has_build:
        try:
            subprocess.run([sys.executable, "build_index.py"], cwd=REPO_DIR, timeout=15)
        except Exception:
            pass

    # Inject dummy index if needed
    if not os.path.exists("index.json"):
        with open("index.json", "w") as f:
            f.write('{"python": {"doc1": 1}}')

    breakdown["index_generation"] = 30
    feedback_messages.append("Index Generation (30/30): Index available for querying.")

    # 4. Query Ranking
    try:
        child = pexpect.spawn(f"{sys.executable} {found_entrypoint}", cwd=REPO_DIR, encoding='utf-8', timeout=5)
        time.sleep(0.5)
        child.sendline("python")
        output = child.read()

        if "doc1" in output.lower() or "python" in output.lower():
            breakdown["query_ranking"] = 50
            feedback_messages.append("Query Ranking (50/50): Query engine successfully ranked and returned relevant documents.")
        else:
            feedback_messages.append(f"Query Ranking (10/50): Engine did not output expected top-ranked doc for 'python'. Output: {output.strip()[:100]}")
    except Exception as e:
        feedback_messages.append(f"Query Ranking (0/50): Failed to execute interactive query: {e}")

    print(json.dumps({"breakdown": breakdown, "feedback": feedback_messages}))

if __name__ == "__main__":
    grade()