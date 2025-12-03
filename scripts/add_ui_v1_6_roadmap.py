# path: scripts/add_ui_v1_6_roadmap.py
# version: v0.1
# purpose: Upsert the UI-v1.6 roadmap item via DB, capturing interaction notes

from __future__ import annotations

"""
Add or update the UI-v1.6 roadmap entry.

This version is for visual/UI polish only.
interaction_notes is used to capture what we learned in this session
so that future Codex runs can reuse the context.
"""

import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.append(project_root)

from backend.db.connection import SessionLocal  # type: ignore
from backend.db.models import RoadmapItem  # type: ignore


VERSION = "UI-v1.6"

GOAL = (
    "Shiroi System の UI を見た目中心で磨き込むフェーズ。"
    "レイアウトや余白・スクロール挙動・テキストエリアの使い勝手など、"
    "実装済み機能の UX を整えることを主目的とする。"
)

CODENAME = "UI Visual Polish v1.6"

DESCRIPTION = (
    "UI-v1.6 では、新機能追加ではなく既存コンソールの見た目と使いやすさの改善に集中する。"
    "特にロードマップ詳細画面（/docs/roadmap/[version]）のレイアウト調整を行い、"
    "interaction_notes 用の大きなメモ欄や、不要な全体スクロールの抑制、"
    "テキストボックスの余白・枠線のトーン調整など、細かな UI 体験を整える。"
)

INTERACTION_NOTES = (
    "このバージョンは「見た目専用」の UI 調整フェーズとして登録。\n"
    "\n"
    "今回のセッションで分かったこと・決めたこと:\n"
    "- ロードマップのソース・オブ・トゥルースは DB の roadmap_items で、docs/roadmap/*.json や "
    "roadmap_dump.json は生成物として扱うこと（AGENTS.md に明記）。\n"
    "- 新しいカラム interaction_notes を RoadmapItem に追加し、各バージョンごとに "
    "「シロイとの会話ログや経緯メモ」を保存できるようにした。\n"
    "- /docs/roadmap/[version] 画面に interaction_notes 用の大きなテキストエリアを追加し、"
    "編集画面に行かなくても直接メモを書いて PATCH /api/roadmap/{version} で保存できるようにした。\n"
    "- テキストエリアは縦長（min-h ベース）で、横幅は 96% + max-w-4xl にし、"
    "左右に少し余白を持たせた。枠線はほとんど主張しない薄いグレー（RGBA指定）にしている。\n"
    "- グローバルなスクロールバーが常時出る問題について、まずは html/body の高さと "
    "overflow、メインレイアウト（flex h-screen / overflow-hidden）を見直しつつ、"
    "最終的には「外側は overflow hidden, 内側 main だけがスクロール」の方針を AGENTS に残した。\n"
    "- PowerShell 環境でのコマンド失敗を減らすため、AGENTS.md に:\n"
    "  - sed や純 bash コマンドを使わないこと\n"
    "  - rg の exit code=1 は“ヒットなし”であってエラー扱いしないこと\n"
    "  - Get-Content / cmd /c type / rg だけを標準ツールとして使うこと\n"
    "  を明示した。\n"
    "\n"
    "このメモ欄（interaction_notes）は、今後 UI バージョンを進めるときに、"
    "「前回どこまで整えたか」「どんな罠があったか（例: Tailwindのクラスや PowerShell 環境）」を "
    "素早く思い出すためのリファレンスとして使う。"
)


def upsert_ui_v1_6() -> None:
    session = SessionLocal()
    try:
        item = session.query(RoadmapItem).filter(RoadmapItem.version == VERSION).first()
        if item is None:
            item = RoadmapItem(
                version=VERSION,
                codename=CODENAME,
                goal=GOAL,
                status="⏳",
                description=DESCRIPTION,
                startDate=None,
                endDate=None,
                progress=0,
                keyFeatures=[],
                dependencies=[],
                metrics=[],
                owner="Frontend / UI",
                documentationLink=None,
                prLink=None,
                development_details=None,
                interaction_notes=INTERACTION_NOTES,
                parent_id=None,
            )
            session.add(item)
            print(f"Created new roadmap item: {VERSION}")
        else:
            # Update text fields in case we refine them later
            item.codename = CODENAME
            item.goal = GOAL
            item.description = DESCRIPTION
            item.interaction_notes = INTERACTION_NOTES
            print(f"Updated existing roadmap item: {VERSION}")
        session.commit()
    finally:
        session.close()


if __name__ == "__main__":
    upsert_ui_v1_6()

