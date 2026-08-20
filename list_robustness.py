import json
with open('roadmap_dump.json', encoding='utf-8') as f:
    rows = json.load(f)
for item in rows:
    if item['version'].startswith('R-'):
        print(item['version'], item['codename'], item['status'], item['progress'])
