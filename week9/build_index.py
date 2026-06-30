import json
with open("index.json", "w") as f:
    json.dump({"python": ["page1"]}, f)
