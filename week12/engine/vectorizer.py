import math
import string
import re

def tokenize(text):
    text = text.lower()
    # Replace punctuation with spaces
    text = re.sub(r'[{}]'.format(re.escape(string.punctuation)), ' ', text)
    return text.split()

def compute_idf(documents):
    N = len(documents)
    df = {}
    for doc in documents:
        unique_terms = set(doc)
        for term in unique_terms:
            df[term] = df.get(term, 0) + 1
            
    idf = {}
    for term, count in df.items():
        # Scikit-learn equivalent formula: log((1 + N) / (1 + count)) + 1
        idf[term] = math.log((1 + N) / (1 + count)) + 1
    return idf

def get_tf_idf_vector(tokens, idf):
    counts = {}
    for t in tokens:
        counts[t] = counts.get(t, 0) + 1
        
    vector = {}
    for term, count in counts.items():
        if term in idf:
            vector[term] = count * idf[term]
            
    # L2 normalize
    sq_sum = sum(w ** 2 for w in vector.values())
    norm = math.sqrt(sq_sum)
    if norm > 0:
        vector = {term: w / norm for term, w in vector.items()}
    return vector

def cosine_similarity(vec1, vec2):
    similarity = 0.0
    for term, val1 in vec1.items():
        if term in vec2:
            similarity += val1 * vec2[term]
    return similarity
