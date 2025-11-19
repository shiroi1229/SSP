import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime

DSN = dict(host='172.25.208.1', dbname='ssp_memory', user='ssp_admin', password='Mizuho0824')
DDL = """
CREATE TABLE IF NOT EXISTS world_timeline_events (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    era TEXT,
    faction TEXT,
    start_year INTEGER NOT NULL,
    end_year INTEGER,
    importance NUMERIC(3,2) DEFAULT 0.5,
    tags JSONB DEFAULT '[]'::jsonb,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
"""
SAMPLES = [
    {
        "title": "黎明評議会の結成",
        "description": "七王国の代表が集い、星辰暦の制定と魔導技術の共有を定めた。",
        "era": "黎明期",
        "faction": "評議会",
        "start_year": 120,
        "end_year": None,
        "importance": 0.92,
        "tags": ['diplomacy', 'magic'],
        "metadata": {"icon": "✨", "location": "ルミナアーク"}
    },
    {
        "title": "紅潮戦役",
        "description": "紅き潮が海を覆い交易が停止。海神と契約した艦隊が鎮圧。",
        "era": "大航海期",
        "faction": "蒼紋艦隊",
        "start_year": 342,
        "end_year": 347,
        "importance": 0.8,
        "tags": ['war', 'navy'],
        "metadata": {"icon": "⚔️"}
    },
    {
        "title": "砂漠図書館の陥落",
        "description": "永炎砂漠の知識庫が『無声の王』により封印。因果グラフが大幅に欠損。",
        "era": "空白紀",
        "faction": "砂漠同盟",
        "start_year": 512,
        "end_year": 513,
        "importance": 0.95,
        "tags": ['catastrophe'],
        "metadata": {"icon": "📚"}
    },
    {
        "title": "天空列車の初走行",
        "description": "浮遊都市を結ぶ列車網が完成。魔導ラインの平和利用が進む。",
        "era": "再興期",
        "faction": "浮遊都市連盟",
        "start_year": 640,
        "end_year": None,
        "importance": 0.7,
        "tags": ['tech', 'transport'],
        "metadata": {"icon": "🚆"}
    },
    {
        "title": "蒼炎継承式",
        "description": "蒼炎の巫女が次代へ力を継承。大陸規模で魔力嵐が沈静化。",
        "era": "再興期",
        "faction": "蒼炎教団",
        "start_year": 702,
        "end_year": None,
        "importance": 0.88,
        "tags": ['ritual'],
        "metadata": {"icon": "🔥"}
    }
]

with psycopg2.connect(**DSN) as conn:
    with conn.cursor() as cur:
        cur.execute(DDL)
        conn.commit()
        cur.execute("SELECT COUNT(*) FROM world_timeline_events")
        count = cur.fetchone()[0]
        if count == 0:
            rows = [(
                sample['title'],
                sample['description'],
                sample['era'],
                sample['faction'],
                sample['start_year'],
                sample['end_year'],
                sample['importance'],
                psycopg2.extras.Json(sample.get('tags', [])),
                psycopg2.extras.Json(sample.get('metadata', {}))
            ) for sample in SAMPLES]
            insert_sql = """
                INSERT INTO world_timeline_events
                    (title, description, era, faction, start_year, end_year, importance, tags, metadata)
                VALUES %s
            """
            execute_values(cur, insert_sql, rows)
            conn.commit()
            print(f"Seeded {len(rows)} timeline events.")
        else:
            print(f"world_timeline_events already has {count} rows, skipping seed.")
