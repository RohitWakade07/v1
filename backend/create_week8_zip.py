import zipfile

with zipfile.ZipFile('week8_test.zip', 'w') as z:
    z.writestr('metadata_organizer/__init__.py', 'def process_corpus(path):\n    return {"document_count": 1}')

print('Created week8_test.zip')
