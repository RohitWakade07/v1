import os, json, subprocess, re, shutil
from pathlib import Path

def _git(args, cwd, timeout=15):
    try:
        r = subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except Exception as e:
        return 1, "", str(e)

def main():
    workspace = Path(".")
    is_github_submission = (workspace / ".git").exists()
    
    if not is_github_submission:
        sub_json = workspace / "submission.json"
        if not sub_json.exists():
            sub_json = workspace / "main.py"
        if not sub_json.exists():
            with open("result.json", "w") as f:
                json.dump({"error": "No submission.json"}, f)
            return

        try:
            payload = json.loads(sub_json.read_text(errors="ignore"))
        except Exception as e:
            with open("result.json", "w") as f:
                json.dump({"error": "Invalid JSON"}, f)
            return

        repo_owner = payload.get("repo_owner", "").strip()
        repo_name = payload.get("repo_name", "").strip()
        token = payload.get("github_token", "").strip()

        if not repo_owner or not repo_name:
            with open("result.json", "w") as f:
                json.dump({"error": "Missing fields"}, f)
            return

        repo_url = f"https://github.com/{repo_owner}/{repo_name}.git"
        if token:
            repo_url = f"https://{token}@github.com/{repo_owner}/{repo_name}.git"

        repo_dir = str(workspace / "_cloned_repo")
        if os.path.exists(repo_dir):
            shutil.rmtree(repo_dir)

        clone_env = os.environ.copy()
        clone_env["GIT_TERMINAL_PROMPT"] = "0"
        
        result = {"clone_ok": False, "clone_error": ""}
        try:
            c = subprocess.run(["git", "clone", "--depth=50", "--no-single-branch", repo_url, repo_dir],
                               capture_output=True, text=True, timeout=60, env=clone_env)
            result["clone_ok"] = (c.returncode == 0)
            if c.returncode != 0:
                err = c.stderr[:200]
                if token:
                    err = err.replace(token, "***")
                result["clone_error"] = err
        except Exception as e:
            result["clone_error"] = str(e)
    else:
        # GitHub Submission - repo is already in the workspace
        repo_dir = str(workspace)
        result = {"clone_ok": True, "clone_error": ""}
        # Attempt to fetch all branches since WorkspaceManager uses depth 1
        subprocess.run(["git", "config", "remote.origin.fetch", "+refs/heads/*:refs/remotes/origin/*"], cwd=repo_dir)
        subprocess.run(["git", "fetch", "--depth=50", "origin"], cwd=repo_dir)

    if result["clone_ok"]:
        conflict_files = []
        conflict_marker_re = re.compile(r"^(<{7}|>{7}|={7}|\|{7})\s", re.MULTILINE)
        for fpath in Path(repo_dir).rglob("*"):
            if fpath.is_file() and ".git" not in fpath.parts:
                try:
                    text = fpath.read_text(errors="ignore")
                    if conflict_marker_re.search(text):
                        conflict_files.append(fpath.name)
                except:
                    pass
        result["conflict_files"] = conflict_files

        rc, log_out, _ = _git(["log", "--oneline", "-20"], repo_dir)
        result["commits"] = [l for l in log_out.splitlines() if l.strip()] if rc == 0 else []

        rc_br, branches_raw, _ = _git(["branch", "-a"], repo_dir)
        result["branches"] = [b.strip() for b in branches_raw.splitlines() if b.strip()]

        rc_mg, merged_log, _ = _git(["log", "--merges", "--oneline", "-5"], repo_dir)
        result["merged_log"] = merged_log.strip() if rc_mg == 0 else ""

        teamwork_files = ["TEAMWORK.md", "teamwork.md", "COLLABORATION.md", "collaboration.md", "CONTRIBUTING.md"]
        teamwork_path = None
        for fname in teamwork_files:
            candidate = Path(repo_dir) / fname
            if candidate.is_file():
                teamwork_path = candidate
                break
        
        result["teamwork_path"] = teamwork_path.name if teamwork_path else None
        if teamwork_path:
            text = teamwork_path.read_text(errors="ignore")
            result["teamwork_words"] = len(text.split())
        else:
            result["teamwork_words"] = 0

        rc_auth, auth_log, _ = _git(["shortlog", "-sn", "--all"], repo_dir)
        result["contributors"] = [l for l in auth_log.splitlines() if l.strip()] if rc_auth == 0 else []
        
        config_path = Path(repo_dir) / "src" / "config.py"
        if config_path.exists():
            result["config_py"] = config_path.read_text(errors="ignore")
        else:
            result["config_py"] = ""
            
        sensors_path = Path(repo_dir) / "src" / "sensors.py"
        if sensors_path.exists():
            result["sensors_py"] = sensors_path.read_text(errors="ignore")
        else:
            result["sensors_py"] = ""
            
        subprocess.run(["pip", "install", "-r", "requirements.txt"], cwd=repo_dir, capture_output=True)
        subprocess.run(["pip", "install", "pytest"], cwd=repo_dir, capture_output=True)
        
        test_run = subprocess.run(["pytest"], cwd=repo_dir, capture_output=True, text=True)
        result["tests_passed"] = (test_run.returncode == 0)
        result["test_output"] = test_run.stdout

    with open("result.json", "w") as f:
        json.dump(result, f)

if __name__ == '__main__':
    main()
