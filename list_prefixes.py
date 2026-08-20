import json
rows=json.load(open('roadmap_dump.json',encoding='utf-8'))
prefixes=sorted(set(item['version'].split('-')[0] for item in rows))
print(prefixes)
