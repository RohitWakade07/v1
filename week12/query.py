import json
import sys
from engine.vectorizer import tokenize, get_tf_idf_vector, cosine_similarity

def main():
    try:
        with open('index.json', 'r', encoding='utf-8') as f:
            index = json.load(f)
    except FileNotFoundError:
        print("index.json not found")
        sys.exit(1)
        
    idf = index.get("idf", {})
    documents = index.get("documents", [])
    
    while True:
        try:
            q = input("Query: ")
            if q.strip().lower() == "quit":
                break
                
            q_tokens = tokenize(q)
            if not q_tokens:
                print("0 documents found.")
                continue
                
            q_vector = get_tf_idf_vector(q_tokens, idf)
            
            results = []
            for doc in documents:
                score = cosine_similarity(q_vector, doc["vector"])
                if score > 0:
                    results.append((score, doc["filename"]))
                    
            results.sort(reverse=True, key=lambda x: (x[0], x[1]))
            
            if not results:
                print("0 documents found.")
            else:
                for score, fname in results[:5]:
                    print(f"{fname} (Score: {score:.4f})")
        except EOFError:
            break

if __name__ == '__main__':
    main()
