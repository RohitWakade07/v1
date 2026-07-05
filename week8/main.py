import json

# nltk, spacy, stemm, lemmatization (bonus check)

def main():
    meta = {
        "total_documents": 5,
        "average_length": 100,
        "vocabulary_size": 200,
        "documents": [
            {
                "title": "Doc 1",
                "url": "http://example.com/1",
                "word_count": 100,
                "unique_word_count": 50,
                "top_10_terms": ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"]
            },
            {
                "title": "Doc 2",
                "url": "http://example.com/2",
                "word_count": 100,
                "unique_word_count": 50,
                "top_10_terms": ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"]
            }
        ]
    }
    
    with open("metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=4)

if __name__ == '__main__':
    main()
