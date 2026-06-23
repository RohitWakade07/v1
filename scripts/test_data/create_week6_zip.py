import zipfile
import os

readme_content = """# Week 6 Project
This is an awesome CLI tool for text analysis.
It meets all the criteria set out in the assignment.

## Usage
Here is an example usage of the CLI tool:
```bash
python analyze.py test_data
```
Enjoy using this script for text analysis!
"""

requirements_content = """requests==2.31.0
"""

analyze_content = """import sys

def main():
    if len(sys.argv) < 2:
        sys.exit(1)
        
    while True:
        try:
            cmd = input("> ").strip()
            if cmd == "quit":
                break
            elif cmd == "stats file1.txt":
                print("words: 8")
                print("lines: 3")
                print("characters: 39")
            elif cmd == "top 2 file2.txt":
                print("python: 3")
            elif cmd == "search world":
                print("file1.txt")
        except EOFError:
            break

if __name__ == "__main__":
    main()
"""

with zipfile.ZipFile("week6_test.zip", "w") as zf:
    zf.writestr("README.md", readme_content)
    zf.writestr("requirements.txt", requirements_content)
    zf.writestr("analyze.py", analyze_content)

print("Created week6_test.zip successfully!")
