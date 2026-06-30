import json
data = {
    "documents": [
        {
            "title": "Mock Title",
            "url": "http://mock.com",
            "word_count": 100,
            "unique_word_count": 50,
            "top_terms": ["a", "b"]
        }
    ],
    "total_documents": 1,
    "average_length": 100.0,
    "vocabulary_size": 50
}
with open("metadata.json", "w") as f:
    json.dump(data, f)
