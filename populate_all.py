import os
import subprocess
import shutil
import zipfile

def run(cmd):
    print(f"Running: {cmd}")
    subprocess.run(cmd, shell=True, check=True)

# 1. Generate all zips
run("python scripts/test_data/generate_test_zips.py")
for w in range(6, 13):
    if os.path.exists(f"scripts/test_data/create_week{w}_zip.py"):
        run(f"python scripts/test_data/create_week{w}_zip.py")

# 2. Switch to git-test
run("git fetch origin")
run("git checkout git-test")
run("git pull origin git-test")

# 3. Extract zips to week folders
mappings = {
    "week1_100_marks.zip": "week1",
    "week2_100_marks.zip": "week2",
    "week3_100_marks.zip": "week3",
    "week4_100_marks.zip": "week4",
}
for w in range(6, 13):
    mappings[f"week{w}_test.zip"] = f"week{w}"

for zip_file, folder in mappings.items():
    if os.path.exists(zip_file):
        if os.path.exists(folder):
            shutil.rmtree(folder)
        os.makedirs(folder, exist_ok=True)
        with zipfile.ZipFile(zip_file, 'r') as zf:
            zf.extractall(folder)
        print(f"Extracted {zip_file} to {folder}")
        os.remove(zip_file)
    else:
        print(f"Warning: {zip_file} not found!")

# 4. For week4, fix the nested dir issue
if os.path.exists("week4/week-04/week-04-nested"):
    src = "week4/week-04/week-04-nested"
    for item in os.listdir(src):
        shutil.move(os.path.join(src, item), "week4")
    shutil.rmtree("week4/week-04")

# 5. Clean up any remaining extra zips
for file in os.listdir("."):
    if file.endswith(".zip"):
        os.remove(file)

# 6. Commit and push
run("git add .")
run("git commit -m 'chore: populate all weeks 1 to 12 with perfect test data'")
run("git push origin git-test")

# 7. Switch back
run("git checkout v1-backend")
print("Done!")
