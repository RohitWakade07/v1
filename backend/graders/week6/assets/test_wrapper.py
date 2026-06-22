import json
import os
import sys
import subprocess

def grade():
    # 1. Grading Variables
    breakdown = {
        "repo_structure": 0,
        "stats_command": 0,
        "top_command": 0,
        "search_command": 0,
        "quit_command": 0
    }
    feedback_messages = []
    
    # We are in the submission dir already, because target_file matched analyze.py
    REPO_DIR = os.getcwd()

    # A. Check Repository Structure (30 pts)
    has_readme = os.path.exists("README.md")
    has_reqs = os.path.exists("requirements.txt")
    
    if has_readme and has_reqs:
        with open("requirements.txt", "r", encoding="utf-8") as f:
            reqs_text = f.read().lower()
        has_requests = "requests" in reqs_text

        with open("README.md", "r", encoding="utf-8") as f:
            readme_text = f.read().lower()
            
        word_count = len(readme_text.split())
        has_usage = "usage" in readme_text or "example" in readme_text
        has_code_block = "```" in readme_text
        
        if word_count >= 30 and has_usage and has_code_block and has_requests:
            breakdown["repo_structure"] = 30
            feedback_messages.append("Repository Structure (30/30): README.md passes quality checks and requirements.txt contains 'requests'.")
        else:
            breakdown["repo_structure"] = 10
            feedback_messages.append(f"Repository Structure (10/30): Quality checks failed. README Words (>=30): {word_count}. Has Usage: {has_usage}. Has Code Blocks: {has_code_block}. Reqs contains 'requests': {has_requests}.")
    else:
        feedback_messages.append(f"Repository Structure (0/30): Missing files. README: {has_readme}, Reqs: {has_reqs}")

    # Verify analyze.py exists
    analyze_path = "analyze.py"
    if not os.path.exists(analyze_path):
        feedback_messages.append("Error: analyze.py not found in the root of the repository.")
        print(json.dumps({"breakdown": breakdown, "feedback": feedback_messages}))
        return

    # B. CLI Interactive Testing (70 pts total)
    test_data_dir = "test_data"
    
    # Prepare all inputs to pipe to stdin
    # The commands to test: stats, top, search, quit
    inputs = "stats file1.txt\ntop 2 file2.txt\nsearch world\nquit\n"
    
    try:
        proc = subprocess.run(
            [sys.executable, "analyze.py", test_data_dir],
            input=inputs,
            capture_output=True,
            text=True,
            timeout=5,
            cwd=REPO_DIR
        )
        
        output = proc.stdout.lower() + proc.stderr.lower()
        
        # We can't cleanly split outputs since prompts and outputs are mixed,
        # but we can look for specific expected substrings in the entire output buffer.

        # Test stats
        if "words: 8" in output and "lines: 3" in output and "characters: 39" in output:
            breakdown["stats_command"] = 20
            feedback_messages.append("stats command (20/20): Output accurate for file1.txt.")
        else:
            feedback_messages.append(f"stats command (0/20): Did not find expected stats in output.")

        # Test top
        if "python: 3" in output or "python : 3" in output or "python 3" in output:
            breakdown["top_command"] = 20
            feedback_messages.append("top command (20/20): Found expected top word 'python' with correct count.")
        else:
            feedback_messages.append(f"top command (0/20): Expected 'python: 3' not found in output.")

        # Test search
        if "file1.txt" in output and "file2.txt" not in output:
            breakdown["search_command"] = 20
            feedback_messages.append("search command (20/20): Correctly identified 'world' only in file1.txt.")
        else:
            feedback_messages.append(f"search command (0/20): Did not list correct files.")

        # Test quit
        # If we reached here and subprocess returned cleanly, quit worked.
        if proc.returncode == 0:
            breakdown["quit_command"] = 10
            feedback_messages.append("quit command (10/10): Handled gracefully and exited.")
        else:
            feedback_messages.append(f"quit command (0/10): Script exited with non-zero code {proc.returncode}.")

    except subprocess.TimeoutExpired:
        feedback_messages.append("CLI Testing Error: Execution timed out. Ensure the script isn't stuck in an infinite loop.")
    except Exception as e:
        feedback_messages.append(f"CLI Testing Error: Unexpected crash during execution: {e}")

    # Output final structured JSON to stdout so the BaseGrader can parse it
    print(json.dumps({"breakdown": breakdown, "feedback": feedback_messages}))

if __name__ == "__main__":
    grade()
