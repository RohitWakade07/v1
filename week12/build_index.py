import json
import os
from engine.vectorizer import tokenize, compute_idf, get_tf_idf_vector

def build():
    corpus_dir = None
    for candidate in ["corpus", "data", "documents", "dataset"]:
        if os.path.isdir(candidate):
            corpus_dir = candidate
            break
            
    if not corpus_dir:
        print("Error: corpus directory not found.")
        return
        
    documents = []
    filenames = []
    
    for f in sorted(os.listdir(corpus_dir)):
        if f.endswith('.json'):
            path = os.path.join(corpus_dir, f)
            with open(path, 'r', encoding='utf-8') as fh:
                doc = json.load(fh)
                content = doc.get('content', '')
                documents.append(tokenize(content))
                filenames.append(f)
                
    if not documents:
        print("No documents found in corpus.")
        return
        
    idf = compute_idf(documents)
    
    # Generate vectors for each document
    doc_vectors = []
    for fname, doc_tokens in zip(filenames, documents):
        vector = get_tf_idf_vector(doc_tokens, idf)
        doc_vectors.append({
            "filename": fname,
            "vector": vector
        })
        
    index = {
        "idf": idf,
        "documents": doc_vectors
    }
    
    with open('index.json', 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False)
    print("Successfully built inverted index.")

if __name__ == '__main__':
    build()