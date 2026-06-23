import zipfile

with zipfile.ZipFile('week9_test.zip', 'w') as z:
    z.writestr('build_index.py', 'import sys; open(sys.argv[2], "w").write("{}")')
    z.writestr('lookup.py', 'print("mock result")')

print('Created week9_test.zip')
