import json
from collections import defaultdict

with open('roadmap_dump.json', encoding='utf-8') as f:
    rows = json.load(f)

by_prefix = defaultdict(list)
for item in rows:
    version = item['version']
    prefix = version.split('-')[0]
    by_prefix[prefix].append(item)

summary = []
for prefix, items in sorted(by_prefix.items()):
    completed = sum(1 for i in items if i['progress'] >= 100)
    in_progress = sum(1 for i in items if 0 < i['progress'] < 100)
    not_started = sum(1 for i in items if i['progress'] == 0)
    summary.append({
        'prefix': prefix,
        'count': len(items),
        'completed': completed,
        'in_progress': in_progress,
        'not_started': not_started
    })

print(json.dumps(summary, ensure_ascii=False, indent=2))
