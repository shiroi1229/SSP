import json
rows=json.load(open('roadmap_dump.json',encoding='utf-8'))
for item in rows:
    if '-' not in item['version']:
        print(item['version'], item['codename'], item['status'], item['progress'])
