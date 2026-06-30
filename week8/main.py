import json
with open('metadata.json', 'w') as f:
  json.dump({'total_documents': 2, 'average_length': 10, 'vocabulary_size': 15, 'documents': [{'title': 'A', 'url': 'B', 'word_count': 1, 'unique_word_count': 1, 'top_terms': ['A']}]}, f)