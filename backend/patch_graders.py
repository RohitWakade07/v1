import os
import shutil
import re

BASE = "a:/eysip/v1/backend/graders"

# 1. Update config.yaml for 8, 9, 10
for week in ["week8", "week9"]:
    config_path = os.path.join(BASE, week, "config.yaml")
    with open(config_path, "r") as f:
        content = f.read()
    content = content.replace('target: "test_corpus"', 'target: "corpus"')
    with open(config_path, "w") as f:
        f.write(content)

# Week 10 config
w10_config = os.path.join(BASE, "week10", "config.yaml")
with open(w10_config, "r") as f:
    w10_content = f.read()
if "test_corpus" not in w10_content:
    w10_content += """  - source: "test_corpus"
    target: "corpus"
"""
with open(w10_config, "w") as f:
    f.write(w10_content)

# Copy test_corpus to week10
w8_corpus = os.path.join(BASE, "week8", "assets", "test_corpus")
w10_corpus = os.path.join(BASE, "week10", "assets", "test_corpus")
if not os.path.exists(w10_corpus):
    shutil.copytree(w8_corpus, w10_corpus)

# 2. Patch Week 9 test_wrapper.py
w9_wrapper = os.path.join(BASE, "week9", "assets", "test_wrapper.py")
with open(w9_wrapper, "r") as f:
    w9_content = f.read()
w9_content = re.sub(
    r'valid_doc_found = .*',
    r'valid_doc_found = "page1" in out_lower',
    w9_content
)
with open(w9_wrapper, "w") as f:
    f.write(w9_content)


# 3. Patch Week 10 test_wrapper.py
w10_wrapper = os.path.join(BASE, "week10", "assets", "test_wrapper.py")
with open(w10_wrapper, "r") as f:
    w10_content = f.read()

# Replace multi-word query
w10_content = w10_content.replace('"machine learning\\nquit\\n"', '"programming language\\nquit\\n"')
w10_content = re.sub(
    r'valid_doc_found = any\(f in out_lower or f.replace\(".json", ""\) in out_lower for f in corpus_files\) if corpus_files else \("doc" in out_lower\)',
    r'valid_doc_found = "page1" in out_lower',
    w10_content
)

# Replace boolean query
w10_content = w10_content.replace('"python AND data\\nquit\\n"', '"python AND linux\\nquit\\n"')
w10_content = re.sub(
    r'valid_doc_found = any\(f in out_lower or f.replace\(".json", ""\) in out_lower for f in corpus_files\) if corpus_files else \("doc" in out_lower\)',
    r'valid_doc_found = "page1" in out_lower or "page2" in out_lower',
    w10_content
)

with open(w10_wrapper, "w") as f:
    f.write(w10_content)

# 4. Patch Week 11 test_wrapper.py
w11_wrapper = os.path.join(BASE, "week11", "assets", "test_wrapper.py")
with open(w11_wrapper, "r") as f:
    w11_content = f.read()

# Make the check more robust to avoid spoofing
robust_check = """
            valid_doc_found = False
            for f in corpus_files:
                doc_name = f.replace(".json", "")
                if doc_name and doc_name != "doc" and (f in out_lower or doc_name in out_lower):
                    valid_doc_found = True
                    break
"""
w11_content = re.sub(
    r'valid_doc_found = any\(f in out_lower or f.replace\(".json", ""\) in out_lower for f in corpus_files\) if corpus_files else \("doc" in out_lower\)',
    robust_check.strip(),
    w11_content
)

with open(w11_wrapper, "w") as f:
    f.write(w11_content)

print("Patching complete.")
