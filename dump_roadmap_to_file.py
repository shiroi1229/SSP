import psycopg2
import json

LIST_FIELDS = ["keyFeatures", "dependencies", "metrics"]
STRING_FIELDS = ["owner", "documentationLink", "prLink", "startDate", "endDate", "development_details"]

with psycopg2.connect(host='172.25.208.1', dbname='ssp_memory', user='ssp_admin', password='Mizuho0824') as conn:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT version, codename, goal, status, progress, description,
                   "startDate", "endDate", "keyFeatures", "dependencies", "metrics",
                   owner, "documentationLink", "prLink", development_details, parent_id
            FROM roadmap_items
            ORDER BY version, codename
        """)
        columns = [desc[0] for desc in cur.description]
        rows = []
        for row in cur.fetchall():
            item = dict(zip(columns, row))
            for field in LIST_FIELDS:
                value = item.get(field)
                if value is None:
                    item[field] = []
                elif isinstance(value, list):
                    item[field] = value
                else:
                    item[field] = [value]
            for field in STRING_FIELDS:
                item[field] = item.get(field) or None
            rows.append(item)

with open('roadmap_dump.json', 'w', encoding='utf-8') as f:
    json.dump(rows, f, ensure_ascii=False, indent=2)

print(f"Exported {len(rows)} items to roadmap_dump.json")
