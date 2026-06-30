import os
import json
import datetime

os.makedirs("corpus", exist_ok=True)
data1 = {
    "title": "Python (programming language)",
    "url": "http://127.0.0.1:8080/wiki/Python_(programming_language)",
    "text": "Python is a high-level, general-purpose programming language.",
    "fetched_at": datetime.datetime.now().isoformat()
}
with open("corpus/1.json", "w") as f:
    json.dump(data1, f)

data2 = {
    "title": "Linux",
    "url": "http://127.0.0.1:8080/wiki/Linux",
    "text": "Linux is a family of open-source Unix-like operating systems.",
    "fetched_at": datetime.datetime.now().isoformat()
}
with open("corpus/2.json", "w") as f:
    json.dump(data2, f)
