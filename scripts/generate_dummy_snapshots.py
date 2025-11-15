import json
from pathlib import Path

snapshots = []
for i in range(5):
    snapshots.append({
        "id": f"snap_{i+1}",
        "created_at": f"2025-11-0{i+1}T12:00:00",
        "short_term": {"prompt": f"サンプル{i+1}"},
        "mid_term": {"evaluation_score": round(0.6 + i * 0.05, 2)},
        "long_term": {"persona": f"v{i+1}"}
    })

Path('data/context_snapshots').mkdir(parents=True, exist_ok=True)
Path('data/context_snapshots/snapshots.json').write_text(
    json.dumps(snapshots, ensure_ascii=False, indent=2),
    encoding='utf-8'
)
