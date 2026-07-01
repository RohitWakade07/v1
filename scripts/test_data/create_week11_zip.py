import zipfile

with zipfile.ZipFile('week11_test.zip', 'w') as z:
    z.writestr('README.md', '# Week 11 Capstone')
    z.writestr('requirements.txt', 'requests')
    z.writestr('engine/__init__.py', '')
    for i in range(50):
        z.writestr(f'corpus/doc{i}.json', '{"url": "mock", "title": "mock", "content": "mock"}')
    z.writestr('main.py', 'print("main")')
    z.writestr('build_index.py', 'open("index.json", "w").write("{}")')
    z.writestr('query.py', 'try:\n  while True: input()\nexcept EOFError: pass\nprint("success")')

print('Created week11_test.zip')
