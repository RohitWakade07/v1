import os
import yaml
import json
import shutil
import subprocess
import sys
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
from graders.registry import get_grader

BASE_DIR = Path("a:/eysip/v1/backend")
GRADERS_DIR = BASE_DIR / "graders"
TEST_WORKSPACE = BASE_DIR / "test_workspace"

def remove_readonly(func, path, excinfo):
    import stat
    os.chmod(path, stat.S_IWRITE)
    func(path)

def cleanup():
    if TEST_WORKSPACE.exists():
        shutil.rmtree(TEST_WORKSPACE, onerror=remove_readonly)

def setup_workspace(week, is_full):
    ws_name = f"test_workspace_w{week}_{'full' if is_full else 'part'}"
    ws = BASE_DIR / ws_name
    if ws.exists():
        shutil.rmtree(ws, onerror=remove_readonly)
    ws.mkdir(parents=True)
    config_path = GRADERS_DIR / f"week{week}" / "config.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    # Copy assets
    assets = config.get("assets", [])
    for asset in assets:
        src = GRADERS_DIR / f"week{week}" / "assets" / asset["source"]
        dst = ws / asset["target"]
        if src.is_dir():
            shutil.copytree(src, dst)
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            
    # Generate mock student files
    generate_mock_files(week, is_full, ws)
    return config, ws

def generate_mock_files(week, is_full, ws):
    if week == 1:
        script = ""
        if is_full:
            script = "mkdir -p eep-software/notes eep-software/scripts eep-software/capstone\n"
            for i in range(1, 13):
                script += f"mkdir -p eep-software/week-{i:02d}\n"
                script += f"touch eep-software/week-{i:02d}/README.md\n"
            script += "echo 'Report' > eep-software/workspace-report.txt\n"
            script += "echo 'alias foo=bar\\nalias baz=qux' > .bashrc\n"
        else:
            script = "mkdir -p eep-software/notes\n"
            script += "mkdir -p eep-software/week-01\n"
        with open(ws / "commands.txt", "w") as f:
            f.write(script)

    elif week == 2:
        script = ""
        if is_full:
            script = "cat server.log | grep 200 > report.txt\n"
            script += "echo '20' >> report.txt\n"
            script += "echo '192.168.1.100' >> report.txt\n"
            script += "echo '/index.html' >> report.txt\n"
            script += "echo '14' >> report.txt\n"
            script += "echo '404' >> report.txt\n"
            script += "echo '500' >> report.txt\n"
        else:
            script = "echo '20' > report.txt\n"
        with open(ws / "analyze.sh", "w") as f:
            f.write(script)

    elif week == 3:
        script = ""
        if is_full:
            script = """#!/bin/bash
DIR=$1
if [ -z "$DIR" ] || [ ! -d "$DIR" ]; then exit 1; fi
mkdir -p "$DIR/Documents" "$DIR/Images" "$DIR/Code" "$DIR/Other"
mv $DIR/*.txt $DIR/*.pdf "$DIR/Documents/" 2>/dev/null
mv $DIR/*.jpg $DIR/*.png "$DIR/Images/" 2>/dev/null
mv $DIR/*.py $DIR/*.sh "$DIR/Code/" 2>/dev/null
mv $DIR/*.csv "$DIR/Other/" 2>/dev/null
echo "Documents: 6 files"
"""
        else:
            script = "exit 0\n"
        with open(ws / "organize.sh", "w") as f:
            f.write(script)

    elif week == 4:
        if is_full:
            (ws / ".gitignore").write_text("*.pyc\\n__pycache__\\n*.log\\n.env")
            (ws / "week-04").mkdir()
            (ws / "week-04" / "README.md").write_text("Hello git")
            subprocess.run(["git", "init"], cwd=ws, capture_output=True)
            subprocess.run(["git", "checkout", "-b", "feature/test"], cwd=ws, capture_output=True)
            subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=ws, capture_output=True)
            subprocess.run(["git", "config", "user.name", "test"], cwd=ws, capture_output=True)
            (ws / "file.py").write_text("print(1)")
            subprocess.run(["git", "add", "."], cwd=ws, capture_output=True)
            for i in range(4):
                (ws / "file.py").write_text(f"print({i})")
                subprocess.run(["git", "commit", "-am", f"feat: add feature {i}"], cwd=ws, capture_output=True)
        else:
            (ws / ".gitignore").write_text("bad")
            subprocess.run(["git", "init"], cwd=ws, capture_output=True)
            
    elif week == 5:
        if is_full:
            payload = {"repo_owner": "test", "repo_name": "test", "pr_number": 1}
            (ws / "submission.json").write_text(json.dumps(payload))
            # We mock the wrapper output instead since cloning fake repos locally will fail
            pass
        else:
            (ws / "submission.json").write_text("{}")
            
    elif week == 6:
        script = ""
        if is_full:
            script = """import sys
if __name__ == '__main__':
    while True:
        try:
            cmd = input()
        except EOFError:
            break
        if cmd == 'quit':
            sys.exit(0)
        elif cmd.startswith('stats'):
            print("Lines Words Characters")
        elif cmd.startswith('search'):
            print("file1.txt")
        elif cmd.startswith('top'):
            print("word: 5")
        else:
            print("Error")
"""
        else:
            script = "import sys\\nsys.exit(0)"
        with open(ws / "analyze.py", "w") as f:
            f.write(script)

    elif week == 7:
        script = ""
        if is_full:
            script = """import os, json
os.makedirs('corpus', exist_ok=True)
for i in range(4):
    with open(f'corpus/page{i}.json', 'w') as f:
        json.dump({"title": "T", "url": "U", "text": "word "*60}, f)
"""
        else:
            script = "pass"
        with open(ws / "collect_wiki.py", "w") as f:
            f.write(script)

    elif week == 8:
        if is_full:
            (ws / "metadata_organizer").mkdir()
            (ws / "metadata_organizer" / "loader.py").write_text("")
            (ws / "metadata_organizer" / "tokenizer.py").write_text("")
            (ws / "metadata_organizer" / "writer.py").write_text("")
            script = """import json
with open('metadata.json', 'w') as f:
    json.dump({"total_documents": 10, "average_length": 5.5, "vocabulary_size": 100, "documents": [{"title":"t", "url":"u", "word_count":1, "unique_word_count":1, "top_10_terms":[]}]}, f)
"""
        else:
            script = "pass"
        with open(ws / "main.py", "w") as f:
            f.write(script)

    elif week == 9:
        if is_full:
            script_build = """import json
with open('index.json', 'w') as f:
    json.dump({"python": {"page1": 5}}, f)
"""
            (ws / "build_index.py").write_text(script_build)
            script_lookup = """import sys
cmd = sys.stdin.read().strip()
if cmd == 'python':
    print('page1')
"""
            (ws / "lookup.py").write_text(script_lookup)
        else:
            (ws / "build_index.py").write_text("pass")
            (ws / "lookup.py").write_text("pass")

    elif week == 10:
        if is_full:
            script = """import sys
cmd = sys.stdin.read().strip()
if 'programming language' in cmd:
    print('page1')
elif 'linux' in cmd:
    print('page2')
"""
        else:
            script = "print('page1')"
        with open(ws / "query.py", "w") as f:
            f.write(script)

    elif week == 11:
        if is_full:
            (ws / "README.md").write_text("Hello")
            (ws / "corpus").mkdir()
            for i in range(4):
                (ws / "corpus" / f"doc{i}.json").write_text("{}")
            (ws / "build_index.py").write_text("open('index.json', 'w').write('{}')")
            script = """import sys
cmd = sys.stdin.read().strip()
print('doc1.json')
"""
            (ws / "query.py").write_text(script)
        else:
            (ws / "README.md").write_text("Hello")
            (ws / "query.py").write_text("pass")

def run_test(week, is_full):
    config, ws = setup_workspace(week, is_full)
    
    # Run test wrapper
    cmd = config["execution_command"].split()
    # Handle bash scripts needing bash
    if cmd[0] == "bash" or cmd[0] == "sh":
        # Check if wrapper exists
        if not (ws / cmd[1]).exists():
            pass # fallback if execution_command is direct

    # Special handling for week 5 mock
    if week == 5:
        if is_full:
            res = {
                "clone_ok": True,
                "conflict_files": [],
                "commits": ["a", "b", "c"],
                "branches": ["feature/test"],
                "teamwork_path": "TEAMWORK.md",
                "teamwork_words": 100,
                "contributors": ["alice", "bob"]
            }
            (ws / "result.json").write_text(json.dumps(res))
        else:
            (ws / "result.json").write_text(json.dumps({"error": "Failed"}))
        rc, stdout, stderr = 0, "", ""
    else:
        try:
            if cmd[0] in ["sh", "bash"] and sys.platform == "win32":
                # Bypass execution for shell scripts on Windows test harness
                rc, stdout, stderr = 0, "", ""
            else:
                r = subprocess.run(
                    cmd,
                    cwd=ws,
                    capture_output=True,
                    text=True,
                    timeout=config.get("timeout_seconds", 30)
                )
                rc, stdout, stderr = r.returncode, r.stdout, r.stderr
        except subprocess.TimeoutExpired:
            rc, stdout, stderr = 124, "", "timeout"

    config["execution_result"] = {
        "exit_code": rc,
        "stdout": stdout,
        "stderr": stderr,
        "timed_out": rc == 124,
        "oom_killed": False
    }

    grader_cls = get_grader(f"week{week}")
    grader = grader_cls(str(ws), str(ws), config)
    res = grader.grade()
    
    return res

results = {}
for w in range(1, 12):
    print(f"Testing Week {w}...")
    full_res = run_test(w, True)
    part_res = run_test(w, False)
    
    results[w] = {
        "full_score": full_res.score,
        "full_max": full_res.max_score,
        "full_pass": full_res.passed,
        "full_feedback": full_res.feedback,
        "part_score": part_res.score,
        "part_max": part_res.max_score,
        "part_pass": part_res.passed,
        "part_feedback": part_res.feedback
    }

print("\\nRESULTS SUMMARY:")
for w, r in results.items():
    print(f"Week {w}:")
    print(f"  Full Solution: {r['full_score']}/{r['full_max']} (Pass: {r['full_pass']})")
    print(f"    Feedback: {r['full_feedback']}")
    print(f"  Part Solution: {r['part_score']}/{r['part_max']} (Pass: {r['part_pass']})")
    print(f"    Feedback: {r['part_feedback']}")

cleanup()
