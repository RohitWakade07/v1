import zipfile

with zipfile.ZipFile('week10_test.zip', 'w') as z:
    z.writestr('README.md', '# Week 10')
    z.writestr('main.py', 'query = input("Query: ")\nif "python" in query.lower(): print("doc1")')
    z.writestr('build_index.py', 'print("Building index...")')

print('Created week10_test.zip')
