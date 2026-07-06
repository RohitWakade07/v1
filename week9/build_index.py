import json
import os

# tfidf, bm25, pickle (bonus features)

def main():
    # just create a simple dummy index
    index_data = {
        "python": {
            "page1": 5,
            "page2": 2
        }
    }
    
    with open("index.json", "w", encoding="utf-8") as f:
        json.dump(index_data, f, indent=4)

if __name__ == '__main__':
    main()
