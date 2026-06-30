import json
with open('index.json','w') as f:
 json.dump({'a': [['d1', 1]]}, f)