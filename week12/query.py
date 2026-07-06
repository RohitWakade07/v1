import pickle
from sklearn.metrics.pairwise import cosine_similarity
import sys

def main():
    try:
        with open('index.pkl', 'rb') as f:
            data = pickle.load(f)
    except FileNotFoundError:
        print("index.pkl not found")
        sys.exit(1)
        
    vectorizer = data['vectorizer']
    matrix = data['matrix']
    filenames = data['filenames']
    
    while True:
        try:
            q = input("Query: ")
            if q.strip().lower() == "quit":
                break
            
            q_vec = vectorizer.transform([q])
            sim = cosine_similarity(q_vec, matrix)[0]
            
            results = [(sim[i], filenames[i]) for i in range(len(filenames)) if sim[i] > 0]
            results.sort(reverse=True)
            
            if not results:
                print("0 documents found.")
            else:
                for score, fname in results[:5]:
                    print(f"{fname} (Score: {score:.4f})")
        except EOFError:
            break

if __name__ == '__main__':
    main()
