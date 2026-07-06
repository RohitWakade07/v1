import json
import os
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer

def build():
    documents = []
    filenames = []
    
    if os.path.isdir('corpus'):
        for f in os.listdir('corpus'):
            if f.endswith('.json'):
                path = os.path.join('corpus', f)
                with open(path, 'r') as fh:
                    doc = json.load(fh)
                    documents.append(doc.get('content', ''))
                    filenames.append(f)
                    
    if not documents:
        documents = ["dummy"]
        filenames = ["dummy"]
        
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(documents)
    
    with open('index.pkl', 'wb') as f:
        pickle.dump({'vectorizer': vectorizer, 'matrix': tfidf_matrix, 'filenames': filenames}, f)
        
if __name__ == '__main__':
    build()