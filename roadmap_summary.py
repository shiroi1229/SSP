import json
from collections import defaultdict

with open('roadmap_dump.json', encoding='utf-8') as f:
    rows = json.load(f)

summary = defaultdict(lambda: {'count':0,'completed':0,'in_progress':0,'not_started':0})
for item in rows:
    prefix = item['version'].split('-')[0]
    summary[prefix]['count'] += 1
    if item['progress'] >= 100:
        summary[prefix]['completed'] += 1
    elif item['progress'] > 0:
        summary[prefix]['in_progress'] += 1
    else:
        summary[prefix]['not_started'] += 1

print(json.dumps(summary, ensure_ascii=False, indent=2))
