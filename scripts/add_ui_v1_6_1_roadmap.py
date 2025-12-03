# path: scripts/add_ui_v1_6_1_roadmap.py
# version: v0.1
# purpose: Upsert UI-v1.6.1 roadmap entry focusing on chat sidebar UX

from __future__ import annotations

"""
Add or update the UI-v1.6.1 roadmap entry.

Purpose: UI-v1.6.1 focuses on Chat-like sidebar and chat UX polish
(ChatGPT-style sidebar: collapsed icons, accessible tooltips, Ctrl/Cmd+K search,
pinning, responsive slide-in) and operational/QA tasks to verify accessibility
and behavior across viewports.

This script upserts a `RoadmapItem` into the DB. Do NOT edit docs/roadmap files
directly; run `python -m backend.scripts.roadmap_doc_sync` after DB changes.
"""

import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.append(project_root)

from backend.db.connection import SessionLocal  # type: ignore
from backend.db.models import RoadmapItem  # type: ignore


VERSION = "UI-v1.6.1"
CODENAME = "Chat Sidebar & UX v1.6.1"

GOAL = (
    "Chat-like sidebar とチャット UX の導入・磨き上げ。"
    "サイドバーの折りたたみ（アイコンのみ）表示、アクセシブルなツールチップ、"
    "グローバル検索(Ctrl/Cmd+K)、ピン機能、新規作成ボタン、モバイル用スライドインを実装し、"
    "インタラクティブ性とキーボード操作性を向上させる。"
)

CODENAME = CODENAME

DESCRIPTION = (
    "UI-v1.6.1 は UI-v1.6 の継続改良で、特にチャット体験に馴染むサイドバー挙動を導入する。"
    "既存のコンポーネントを壊さずに段階的に機能を追加し、アクセシビリティ、レスポンシブ、テストを重視する。"
)

INTERACTION_NOTES = (
    "Purpose:\n"
    " - Chat-like sidebar UX: collapsed icons + keyboard-accessible tooltips, Ctrl/Cmd+K search, pinning, New button, responsive slide-in.\n"
    " - Improve discoverability and speed for chat workflows (new chat, jump-to).\n\n"
    "Planned Work Items (implementation plan):\n"
    " 1) Sidebar: collapsed icon-only mode + accessible tooltip component.\n"
    "    - Add `aria-*` attributes, ensure Tab focus shows tooltip.\n"
    " 2) Global Search: top-of-sidebar search input and global keybinding (Ctrl/Cmd+K).\n"
    "    - Implement a lightweight search index (client-side for routes), fallback to server search.\n"
    " 3) New & Pin: Add New button (create chat/page) and pin/unpin per item (localStorage).\n"
    " 4) Responsive: mobile slide-in sidebar, close on outside click, support swipe open/close.\n"
    " 5) Tests & QA: Playwright smoke tests for sidebar keyboard flow, accessibility checks (axe).\n\n"
    "Acceptance Criteria:\n"
    " - Collapsed sidebar shows icons only; Tab focus reveals tooltip and aria-current for active link.\n"
    " - Ctrl/Cmd+K opens search and focuses input; typing navigates to matching routes.\n"
    " - Pin state persists in localStorage across reloads.\n"
    " - Mobile: sidebar slides in/out; content behind is inert while open.\n"
    " - Automated Playwright tests pass in CI for main flows.\n\n"
    "Developer Notes:\n"
    " - Do not edit `docs/roadmap/*.json` manually. After DB upsert, run `python -m backend.scripts.roadmap_doc_sync`.\n"
    " - Recommended UI files: `frontend/components/layout/Sidebar.tsx`, `frontend/app/layout.tsx`, `frontend/styles` (Tailwind config).\n"
    " - Add Playwright tests under `frontend/tests/playwright` and a GitHub action to run them.\n\n"
    "Apply Steps (safe):\n"
    " 1. Create branch `feat/ui-v1.6.1-sidebar`\n"
    " 2. Implement changes and run `npm run dev --prefix frontend` locally.\n"
    " 3. Run Playwright locally (or `npx playwright test`) to validate.\n"
    " 4. Upsert roadmap item with this script, then run `python -m backend.scripts.roadmap_doc_sync`.\n"
    " 5. Commit changes and open PR for review.\n"
)


def upsert_ui_v1_6_1() -> None:
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
                keyFeatures=[
                    "Collapsed icon-only sidebar with accessible tooltips",
                    "Global search (Ctrl/Cmd+K) in sidebar",
                    "Pin/unpin and New button for quick chats/pages",
                    "Mobile slide-in sidebar and responsive behavior",
                    "Playwright based smoke tests and accessibility checks",
                ],
                dependencies=["frontend/layout", "frontend/components/layout/Sidebar.tsx"],
                metrics=["Time-to-new-chat (s)", "Sidebar keyboard success rate", "Playwright test pass"],
                owner="Frontend / UX",
                documentationLink=None,
                prLink=None,
                development_details=None,
                interaction_notes=INTERACTION_NOTES,
                parent_id=None,
            )
            session.add(item)
            print(f"Created new roadmap item: {VERSION}")
        else:
            item.codename = CODENAME
            item.goal = GOAL
            item.description = DESCRIPTION
            item.interaction_notes = INTERACTION_NOTES
            # update keyFeatures/metrics if desired
            item.keyFeatures = [
                "Collapsed icon-only sidebar with accessible tooltips",
                "Global search (Ctrl/Cmd+K) in sidebar",
                "Pin/unpin and New button for quick chats/pages",
                "Mobile slide-in sidebar and responsive behavior",
                "Playwright based smoke tests and accessibility checks",
            ]
            item.dependencies = ["frontend/layout", "frontend/components/layout/Sidebar.tsx"]
            item.metrics = ["Time-to-new-chat (s)", "Sidebar keyboard success rate", "Playwright test pass"]
            print(f"Updated existing roadmap item: {VERSION}")
        session.commit()
    finally:
        session.close()


if __name__ == "__main__":
    upsert_ui_v1_6_1()
