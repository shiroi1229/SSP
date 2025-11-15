import json
rows=json.load(open('roadmap_dump.json',encoding='utf-8'))
for prefix in ['A','R','UI','Backend','B','C']:
    items=[r for r in rows if r['version'].startswith(prefix+'-')]
    if not items:
        continue
    print(prefix, len(items))
    for item in items:
        print(' ', item['version'], item['codename'], item['status'], item['progress'])
