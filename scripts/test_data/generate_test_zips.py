"""
Test ZIP generator for all weeks (1-4).

Week 1 - Workspace Setup:
  Full marks : all 12 week dirs + 3 struct dirs + 12 READMEs + workspace-report.txt + .bashrc (2 aliases)
  Partial    : only 6 week dirs, no structural dirs, no workspace-report.txt, no .bashrc

Week 2 - Log Analyzer:
  Full marks : analyze.sh that correctly processes server.log → report.txt with exact expected values
  Partial    : analyze.sh that creates report.txt but only shows total count (no IPs/URLs)

Week 3 - File Organizer:
  Full marks : organize.sh that correctly moves all 15 files and handles error cases
  Partial    : organize.sh that only moves .txt files

Week 4 - Python Calculator:
  Full marks : calculator.py that handles +, -, *, /
  Partial    : calculator.py that only handles + and -
"""

import os
import zipfile


# ─────────────────────────────────────────────────────────────────────────────
# WEEK 1 – Workspace Setup
# The grader runs: bash commands.txt
# Full marks  : commands.txt creates 12 week dirs + 3 struct dirs + 12 READMEs + workspace-report.txt + .bashrc
# Partial     : commands.txt creates only 6 week dirs
# ─────────────────────────────────────────────────────────────────────────────

COMMANDS_TXT_FULL = """mkdir -p eep-software
mkdir -p eep-software/week-01
mkdir -p eep-software/week-02
mkdir -p eep-software/week-03
mkdir -p eep-software/week-04
mkdir -p eep-software/week-05
mkdir -p eep-software/week-06
mkdir -p eep-software/week-07
mkdir -p eep-software/week-08
mkdir -p eep-software/week-09
mkdir -p eep-software/week-10
mkdir -p eep-software/week-11
mkdir -p eep-software/week-12
mkdir -p eep-software/notes
mkdir -p eep-software/scripts
mkdir -p eep-software/capstone
echo "# Week 01" > eep-software/week-01/README.md
echo "# Week 02" > eep-software/week-02/README.md
echo "# Week 03" > eep-software/week-03/README.md
echo "# Week 04" > eep-software/week-04/README.md
echo "# Week 05" > eep-software/week-05/README.md
echo "# Week 06" > eep-software/week-06/README.md
echo "# Week 07" > eep-software/week-07/README.md
echo "# Week 08" > eep-software/week-08/README.md
echo "# Week 09" > eep-software/week-09/README.md
echo "# Week 10" > eep-software/week-10/README.md
echo "# Week 11" > eep-software/week-11/README.md
echo "# Week 12" > eep-software/week-12/README.md
echo "Directory tree of eep-software workspace" > eep-software/workspace-report.txt
echo "alias ll='ls -al'" > .bashrc
echo "alias gs='git status'" >> .bashrc
"""

COMMANDS_TXT_PARTIAL = """mkdir -p eep-software
mkdir -p eep-software/week-01
mkdir -p eep-software/week-02
mkdir -p eep-software/week-03
mkdir -p eep-software/week-04
mkdir -p eep-software/week-05
mkdir -p eep-software/week-06
echo "# Week 01" > eep-software/week-01/README.md
echo "# Week 02" > eep-software/week-02/README.md
echo "# Week 03" > eep-software/week-03/README.md
echo "# Week 04" > eep-software/week-04/README.md
echo "# Week 05" > eep-software/week-05/README.md
echo "# Week 06" > eep-software/week-06/README.md
"""

def create_week1_full():
    with zipfile.ZipFile("week1_100_marks.zip", "w") as zf:
        zf.writestr("commands.txt", COMMANDS_TXT_FULL)
    print("Created week1_100_marks.zip")

def create_week1_partial():
    with zipfile.ZipFile("week1_partial_marks.zip", "w") as zf:
        zf.writestr("commands.txt", COMMANDS_TXT_PARTIAL)
    print("Created week1_partial_marks.zip")


# ─────────────────────────────────────────────────────────────────────────────
# WEEK 2 – Log Analyzer
# The grader injects server.log (20 requests, top IP=192.168.1.100, top URL=/index.html)
# Full marks  : analyze.sh that extracts all required info and writes to report.txt
# Partial     : analyze.sh that only counts total requests
# ─────────────────────────────────────────────────────────────────────────────

ANALYZE_SH_FULL = r"""#!/bin/bash
# Analyzes server.log and writes report.txt

LOG="server.log"
OUT="report.txt"

echo "=== Log Analysis Report ===" > "$OUT"
echo "" >> "$OUT"

# Total requests
TOTAL=$(wc -l < "$LOG")
echo "Total Requests: $TOTAL" >> "$OUT"
echo "" >> "$OUT"

# Top 3 IP addresses
echo "Top IP Addresses:" >> "$OUT"
awk '{print $1}' "$LOG" | sort | uniq -c | sort -rn | head -3 >> "$OUT"
echo "" >> "$OUT"

# Top 3 requested URLs
echo "Top URLs:" >> "$OUT"
awk '{print $7}' "$LOG" | sort | uniq -c | sort -rn | head -3 >> "$OUT"
echo "" >> "$OUT"

# HTTP status code distribution
echo "Status Code Distribution:" >> "$OUT"
awk '{print $9}' "$LOG" | sort | uniq -c | sort -rn >> "$OUT"
"""

ANALYZE_SH_PARTIAL = r"""#!/bin/bash
# Analyzes server.log - only counts total requests
LOG="server.log"
OUT="report.txt"
TOTAL=$(wc -l < "$LOG")
echo "Total Requests: $TOTAL" > "$OUT"
"""


def create_week2_full():
    with zipfile.ZipFile("week2_100_marks.zip", "w") as zf:
        zf.writestr("analyze.sh", ANALYZE_SH_FULL)
    print("Created week2_100_marks.zip")


def create_week2_partial():
    with zipfile.ZipFile("week2_partial_marks.zip", "w") as zf:
        zf.writestr("analyze.sh", ANALYZE_SH_PARTIAL)
    print("Created week2_partial_marks.zip")


# ─────────────────────────────────────────────────────────────────────────────
# WEEK 3 – File Organizer
# The grader injects test_mixed/ with 15 known files.
# Full marks  : organize.sh that moves ALL files by extension + handles error cases
# Partial     : organize.sh that only moves .txt files
# ─────────────────────────────────────────────────────────────────────────────

ORGANIZE_SH_FULL = r"""#!/bin/bash
# Organizes files in a directory by extension

if [ $# -ne 1 ]; then
    echo "Usage: $0 <directory>" >&2
    exit 1
fi

DIR="$1"

if [ ! -d "$DIR" ]; then
    echo "Error: '$DIR' is not a directory." >&2
    exit 1
fi

mkdir -p "$DIR/Documents" "$DIR/Images" "$DIR/Code" "$DIR/Other"

docs=0; imgs=0; code=0; other=0

for file in "$DIR"/*; do
    [ -f "$file" ] || continue
    ext="${file##*.}"
    case "${ext,,}" in
        txt|pdf)  mv "$file" "$DIR/Documents/"; ((docs++)) ;;
        jpg|png)  mv "$file" "$DIR/Images/";    ((imgs++)) ;;
        py|sh)    mv "$file" "$DIR/Code/";      ((code++)) ;;
        *)        mv "$file" "$DIR/Other/";     ((other++)) ;;
    esac
done

echo "Documents: $docs files"
echo "Images: $imgs files"
echo "Code: $code files"
echo "Other: $other files"
"""

ORGANIZE_SH_PARTIAL = r"""#!/bin/bash
# Only moves .txt files

if [ $# -ne 1 ]; then
    echo "Usage: $0 <directory>" >&2
    exit 1
fi

DIR="$1"

if [ ! -d "$DIR" ]; then
    echo "Error: '$DIR' not found." >&2
    exit 1
fi

mkdir -p "$DIR/Documents"

count=0
for file in "$DIR"/*.txt; do
    [ -f "$file" ] && mv "$file" "$DIR/Documents/" && ((count++))
done

echo "Documents: $count files"
"""


def create_week3_full():
    with zipfile.ZipFile("week3_100_marks.zip", "w") as zf:
        zf.writestr("organize.sh", ORGANIZE_SH_FULL)
    print("Created week3_100_marks.zip")


def create_week3_partial():
    with zipfile.ZipFile("week3_partial_marks.zip", "w") as zf:
        zf.writestr("organize.sh", ORGANIZE_SH_PARTIAL)
    print("Created week3_partial_marks.zip")


# ─────────────────────────────────────────────────────────────────────────────
# WEEK 4 – Git Recovery Challenge
# Full marks  : .git exists, RECOVERY.md exists, .gitignore ignores .log, working tree clean, history > 1 commit
# Partial     : .git exists, but a .log file is tracked and working tree dirty
# ─────────────────────────────────────────────────────────────────────────────

import tempfile
import subprocess
import shutil

def create_week4_full():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Initialize git and set local config
        subprocess.run(["git", "init"], cwd=tmpdir, check=True, stdout=subprocess.DEVNULL)
        subprocess.run(["git", "config", "user.name", "Test Student"], cwd=tmpdir, check=True)
        subprocess.run(["git", "config", "user.email", "student@test.com"], cwd=tmpdir, check=True)
        
        # Create initial commit
        with open(os.path.join(tmpdir, "main.py"), "w") as f:
            f.write("print('Hello world')")
        subprocess.run(["git", "add", "main.py"], cwd=tmpdir, check=True)
        subprocess.run(["git", "commit", "-m", "Initial commt with typo"], cwd=tmpdir, check=True, stdout=subprocess.DEVNULL)
        
        # Create .gitignore and RECOVERY.md
        with open(os.path.join(tmpdir, ".gitignore"), "w") as f:
            f.write("*.log\n*.bin\n")
        with open(os.path.join(tmpdir, "RECOVERY.md"), "w") as f:
            f.write("# Git Recovery\nI successfully cleaned the repository.\n")
            
        # Amend commit and add new files
        subprocess.run(["git", "add", ".gitignore", "RECOVERY.md"], cwd=tmpdir, check=True)
        subprocess.run(["git", "commit", "--amend", "-m", "Initial commit (fixed typo) and added recovery docs"], cwd=tmpdir, check=True, stdout=subprocess.DEVNULL)
        
        # Add another commit to ensure history > 1
        with open(os.path.join(tmpdir, "another.txt"), "w") as f:
            f.write("Some text")
        subprocess.run(["git", "add", "another.txt"], cwd=tmpdir, check=True)
        subprocess.run(["git", "commit", "-m", "Second commit"], cwd=tmpdir, check=True, stdout=subprocess.DEVNULL)
        
        # Zip it up with a nested folder structure to prove target discovery works!
        nest_dir = "week-04/week-04-nested"
        with zipfile.ZipFile("week4_100_marks.zip", "w") as zf:
            for root, dirs, files in os.walk(tmpdir):
                for file in files:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, tmpdir)
                    zf.write(file_path, arcname=os.path.join(nest_dir, rel_path))
    print("Created week4_100_marks.zip")


def create_week4_partial():
    with tempfile.TemporaryDirectory() as tmpdir:
        subprocess.run(["git", "init"], cwd=tmpdir, check=True, stdout=subprocess.DEVNULL)
        subprocess.run(["git", "config", "user.name", "Test Student"], cwd=tmpdir, check=True)
        subprocess.run(["git", "config", "user.email", "student@test.com"], cwd=tmpdir, check=True)
        
        # Create .gitignore and RECOVERY.md
        with open(os.path.join(tmpdir, ".gitignore"), "w") as f:
            f.write("*.exe\n")  # Missing *.log
        with open(os.path.join(tmpdir, "RECOVERY.md"), "w") as f:
            f.write("# Recovery Docs")
            
        # Create a log file and ACTUALLY track it (this will fail the index check)
        with open(os.path.join(tmpdir, "error.log"), "w") as f:
            f.write("Error occurred")
            
        subprocess.run(["git", "add", "RECOVERY.md", ".gitignore", "error.log"], cwd=tmpdir, check=True)
        subprocess.run(["git", "commit", "-m", "Commit with log file"], cwd=tmpdir, check=True, stdout=subprocess.DEVNULL)
        
        # Create dirty working tree (this will fail the clean tree check)
        with open(os.path.join(tmpdir, "RECOVERY.md"), "a") as f:
            f.write("\nUncommitted change")
            
        # Zip it up
        nest_dir = "week-04"
        with zipfile.ZipFile("week4_partial_marks.zip", "w") as zf:
            for root, dirs, files in os.walk(tmpdir):
                for file in files:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, tmpdir)
                    zf.write(file_path, arcname=os.path.join(nest_dir, rel_path))
    print("Created week4_partial_marks.zip")

# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    create_week1_full()
    create_week1_partial()
    create_week2_full()
    create_week2_partial()
    create_week3_full()
    create_week3_partial()
    create_week4_full()
    create_week4_partial()
    print("\nAll test ZIPs generated successfully.")
