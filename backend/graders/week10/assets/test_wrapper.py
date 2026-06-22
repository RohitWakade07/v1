import json, os
def grade():
    breakdown = {"readme": 0}
    if os.path.exists("README.md"):
        breakdown["readme"] = 100
        print(json.dumps({"breakdown": breakdown, "feedback": ["Found README.md"]}))
    else:
        print(json.dumps({"breakdown": breakdown, "feedback": ["Missing README.md"]}))
if __name__ == "__main__":
    grade()
