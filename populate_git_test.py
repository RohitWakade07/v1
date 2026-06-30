import os
import subprocess
import shutil
import zipfile

def run(cmd):
    print(f"Running: {cmd}")
    subprocess.run(cmd, shell=True, check=True)

# 1. Generate all zips
run("python scripts/test_data/generate_test_zips.py")
run("python scripts/test_data/create_week6_zip.py")
run("python scripts/test_data/create_week7_zip.py")
run("python scripts/test_data/create_week8_zip.py")
run("python scripts/test_data/create_week9_zip.py")

# 2. Switch to git-test
run("git checkout git-test")
run("git pull origin git-test")

# 3. Extract zips to week folders
mappings = {
    "week2_100_marks.zip": "week2",
    "week3_100_marks.zip": "week3",
    "week4_100_marks.zip": "week4",
    "week6_test.zip": "week6",
    "week7_test.zip": "week7",
    "week8_test.zip": "week8",
    "week9_test.zip": "week9",
}

for zip_file, folder in mappings.items():
    if os.path.exists(folder):
        shutil.rmtree(folder)
    os.makedirs(folder, exist_ok=True)
    with zipfile.ZipFile(zip_file, 'r') as zf:
        zf.extractall(folder)
    print(f"Extracted {zip_file} to {folder}")

# 4. For week4, we must rename week-04/week-04-nested to . if it exists, because the python zip script nested it.
# Actually, the zip script creates week-04/week-04-nested with a .git repo.
# For git-test branch, the user will submit `https://.../tree/git-test/week4`
# So week4 needs to contain the .git repo.
if os.path.exists("week4/week-04/week-04-nested"):
    # move contents up
    src = "week4/week-04/week-04-nested"
    for item in os.listdir(src):
        shutil.move(os.path.join(src, item), "week4")
    shutil.rmtree("week4/week-04")

# 5. Clean up zips
for zip_file in mappings.keys():
    if os.path.exists(zip_file):
        os.remove(zip_file)
if os.path.exists("week1_100_marks.zip"): os.remove("week1_100_marks.zip")
if os.path.exists("week1_partial_marks.zip"): os.remove("week1_partial_marks.zip")
if os.path.exists("week2_partial_marks.zip"): os.remove("week2_partial_marks.zip")
if os.path.exists("week3_partial_marks.zip"): os.remove("week3_partial_marks.zip")
if os.path.exists("week4_partial_marks.zip"): os.remove("week4_partial_marks.zip")

# 6. Commit and push
run("git add .")
run("git commit -m 'chore: mock all weeks with perfect submission files'")
run("git push origin git-test")

# 7. Switch back
run("git checkout v1-backend")
print("Done!")
