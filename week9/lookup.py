import sys
import json

def main():
    query = sys.stdin.read().strip().lower()
    
    try:
        with open("index.json", "r", encoding="utf-8") as f:
            index_data = json.load(f)
    except:
        index_data = {}
        
    if query in index_data:
        for doc in index_data[query]:
            print(doc)
    else:
        print("not found")

if __name__ == '__main__':
    main()
