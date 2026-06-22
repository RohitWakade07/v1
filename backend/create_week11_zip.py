import zipfile

with zipfile.ZipFile('week11_test.zip', 'w') as z:
    z.writestr('README.md', '# Week 11 Capstone')
    z.writestr('requirements.txt', 'requests')
    z.writestr('engine/__init__.py', '')
    for i in range(50):
        z.writestr(f'corpus/doc{i}.json', '{"url": "mock", "title": "mock", "content": "mock"}')
    z.writestr('main.py', 'query = input("Query: ")\nif "mock article" in query.lower(): print("doc5")\nif "python" in query.lower(): print("doc1")')
    z.writestr('build_index.py', 'print("Building index...")')

print('Created week11_test.zip')
