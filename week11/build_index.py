import json

index = {
    "test": {"doc1": 1},
    "query2": {"doc2": 1}
}

with open("index.json", "w") as f:
    json.dump(index, f)
