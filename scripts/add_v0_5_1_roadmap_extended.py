import json
import os
import sys
from pathlib import Path

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

from backend.db.connection import SessionLocal  # type: ignore
from backend.db.models import RoadmapItem  # type: ignore


def upsert_backend_items() -> None:
    """
    v0.5.1 / v0.5.1_PoC を system_roadmap_extended.json と DB に追加する。
    system_roadmap.json は既に構造が不安定なため、ここでは拡張版のみを対象にする。
    """
    roadmap_path = Path("docs/roadmap/system_roadmap_extended.json")
    data = json.loads(roadmap_path.read_text(encoding="utf-8"))

    backend = data.get("backend", [])

    def has_version(v: str) -> bool:
        return any(item.get("version") == v for item in backend)

    try:
        idx_v05 = next(i for i, item in enumerate(backend) if item.get("version") == "v0.5")
    except StopIteration:
        raise SystemExit("v0.5 entry not found in extended roadmap; aborting.")

    # v0.5.1 本番恒久版
    if not has_version("v0.5.1"):
        v05_1 = {
            "version": "v0.5.1",
            "codename": "Knowledge Viewer Permanent",
            "goal": "v0.5 Knowledge Viewer を本番環境で恒久運用できるようにし、RAG 検索結果の可視性・応答速度・安定性を高める。",
            "status": "⚪",
            "description": (
                "v0.5.1 では、v0.5 で実装した Knowledge Viewer を一時的な PoC UI から本番運用前提の恒久仕様へ引き上げる。"
                " 大量のコンテキストを扱った際のページング・フィルタ・ソートの操作性、RAG API のレスポンス遅延、"
                "および 404/500 系エラー時のリトライやエラーメッセージ表示を整備し、RAG 由来の「どのドキュメントが答えに効いているか」を"
                "安定して追跡できる状態を目指す。"
            ),
            "startDate": "2025-12-01",
            "endDate": "2025-12-10",
            "progress": 0,
            "keyFeatures": [
                "backend/api/knowledge.py — /api/knowledge, /api/knowledge/search の安定化（ページング・フィルタ・エラー時のレスポンス整形）。",
                "frontend/app/knowledge/page.tsx — Knowledge Viewer 恒久版 UI。大量件数のコンテキストを扱うためのテーブル操作性を改善。",
                "frontend/components/KnowledgeTable.tsx — カラム定義・ソート・ページング・行クリック時の詳細表示。",
                "modules/rag_engine.py — RAG 検索のコアロジック。クエリ／フィルタ条件の追加とログ出力。",
            ],
            "dependencies": [
                "v0.3 Contracted I/O Model",
                "v0.5 Knowledge Viewer",
            ],
            "metrics": [
                "Knowledge API (/api/knowledge, /api/knowledge/search) の成功率 99.5%以上。",
                "RAG 検索レスポンス p95 < 800ms。",
                "Knowledge Viewer 画面でのページング・フィルタ操作時の JS エラー 0 件。",
            ],
            "owner": "Backend Core / Knowledge Viewer",
            "documentationLink": "docs/operations/v0_5_1_permanent_spec.md",
            "development_details": (
                "v0.5 で実装した Knowledge Viewer を前提に、API のバリデーション強化と UI のテーブル操作性を見直す。"
                " まず backend/api/knowledge.py でクエリパラメータの検証とページングロジックを明示し、"
                " modules/rag_engine.py で検索条件とログ出力を整理する。"
                " 次に frontend/app/knowledge/page.tsx と KnowledgeTable.tsx でフィルタ・ソート UI を恒久運用向けに整え、"
                " 500 系エラー時のリトライガイドや空状態のメッセージを追加する。"
            ),
            "parent_id": None,
        }
        backend.insert(idx_v05 + 1, v05_1)

    # v0.5.1_PoC 検証版
    if not has_version("v0.5.1_PoC"):
        v05_1_poc = {
            "version": "v0.5.1_PoC",
            "codename": "Knowledge Viewer PoC",
            "goal": "v0.5 / v0.5.1 の Knowledge Viewer が、実データと負荷を想定した条件で KPI を満たすかを PoC で検証する。",
            "status": "⚪",
            "description": (
                "PoC 用のシナリオランナーから /api/knowledge /api/knowledge/search を繰り返し叩き、"
                " レスポンス時間・成功率・エラー発生時の UI 表示を計測する。"
                " 得られたメトリクスを docs/operations/v0_5_1_poc_report.md に記録し、"
                " 本番運用に必要なキャッシュ戦略やインデックス設計の見直しポイントを洗い出す。"
            ),
            "startDate": "2025-12-10",
            "endDate": "2025-12-20",
            "progress": 0,
            "keyFeatures": [
                "docs/operations/v0_5_1_poc_plan.md — Knowledge Viewer PoC の評価観点・テストシナリオ・合格基準。",
                "tools/v0_5_1_knowledge_poc_runner.py — /api/knowledge 系 API を一定間隔で叩き、JSONL にログを蓄積するランナー。",
                "docs/operations/v0_5_1_poc_report.md — 実測値と考察を記録する PoC レポート。",
                "frontend/app/knowledge/page.tsx — PoC 実行時に確認する UI（エラー表示・ローディング挙動・RAG ソース表示）。",
            ],
            "dependencies": [
                "v0.5 Knowledge Viewer",
                "v0.5.1 Knowledge Viewer Permanent",
                "backend/api/knowledge.py",
                "frontend/app/knowledge/page.tsx",
            ],
            "metrics": [
                "PoC 実行中の /api/knowledge /api/knowledge/search の成功率 99% 以上。",
                "PoC ログ上での p95 レスポンス時間 < 1.0 秒。",
                "UI の表示崩れや致命的な JS エラー 0 件。",
            ],
            "owner": "Backend Core / Knowledge Viewer",
            "documentationLink": "docs/operations/v0_5_1_poc_report.md",
            "development_details": (
                "v0.5.1 の恒久仕様を前提に、PoC ランナー tools/v0_5_1_knowledge_poc_runner.py から一定時間負荷をかける。"
                " ログは logs/v0_5_1_knowledge_poc.jsonl などに蓄積し、レスポンスコード・応答時間・エラーメッセージを集計する。"
                " その結果を docs/operations/v0_5_1_poc_report.md にまとめ、インデックスやキャッシュ設定の調整が必要かどうかを判断する。"
            ),
            "parent_id": None,
        }

        # v0.5.1 に続けて挿入するため、改めて位置を計算
        idx_after_v05 = next(i for i, item in enumerate(backend) if item.get("version") == "v0.5.1")
        backend.insert(idx_after_v05 + 1, v05_1_poc)

    data["backend"] = backend
    roadmap_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def upsert_db_items() -> None:
    session = SessionLocal()
    try:
        def ensure_item(version: str, **kwargs) -> None:
            item = session.query(RoadmapItem).filter_by(version=version).first()
            if item is None:
                item = RoadmapItem(version=version, **kwargs)
                session.add(item)
            else:
                for k, v in kwargs.items():
                    setattr(item, k, v)

        ensure_item(
            "v0.5.1",
            codename="Knowledge Viewer Permanent",
            goal="v0.5 Knowledge Viewer を本番環境で恒久運用できるようにし、RAG 検索結果の可視性・応答速度・安定性を高める。",
            status="⚪",
            description=(
                "v0.5 で実装した Knowledge Viewer を一時的な PoC UI から本番運用前提の恒久仕様へ引き上げる。"
                " 大量のコンテキストを扱った際のページング・フィルタ・ソートの操作性、RAG API のレスポンス遅延、"
                "および 404/500 系エラー時のリトライやエラーメッセージ表示を整備し、"
                "RAG 由来の「どのドキュメントが答えに効いているか」を安定して追跡できる状態を目指す。"
            ),
            startDate="2025-12-01",
            endDate="2025-12-10",
            progress=0,
            keyFeatures=[
                "backend/api/knowledge.py",
                "frontend/app/knowledge/page.tsx",
                "frontend/components/KnowledgeTable.tsx",
                "modules/rag_engine.py",
            ],
            dependencies=[
                "v0.3 Contracted I/O Model",
                "v0.5 Knowledge Viewer",
            ],
            metrics=[
                "Knowledge API 成功率 99.5%以上",
                "RAG 検索レスポンス p95 < 800ms",
                "Knowledge Viewer 画面での JS エラー 0 件",
            ],
            owner="Backend Core / Knowledge Viewer",
            documentationLink="docs/operations/v0_5_1_permanent_spec.md",
            prLink=None,
            development_details="v0.5 の Knowledge Viewer 実装をベースに、API と UI の恒久運用仕様を固めるエピック。詳細は docs/operations/v0_5_1_permanent_spec.md に記載する。",
            parent_id=None,
        )

        ensure_item(
            "v0.5.1_PoC",
            codename="Knowledge Viewer PoC",
            goal="v0.5 / v0.5.1 の Knowledge Viewer が、実データと負荷を想定した条件で KPI を満たすかを PoC で検証する。",
            status="⚪",
            description=(
                "PoC 用のシナリオランナーから /api/knowledge /api/knowledge/search を繰り返し叩き、"
                " レスポンス時間・成功率・エラー発生時の UI 表示を計測する。"
                " 得られたメトリクスを docs/operations/v0_5_1_poc_report.md に記録し、"
                " 本番運用に必要なキャッシュ戦略やインデックス設計の見直しポイントを洗い出す。"
            ),
            startDate="2025-12-10",
            endDate="2025-12-20",
            progress=0,
            keyFeatures=[
                "docs/operations/v0_5_1_poc_plan.md",
                "tools/v0_5_1_knowledge_poc_runner.py",
                "docs/operations/v0_5_1_poc_report.md",
                "frontend/app/knowledge/page.tsx",
            ],
            dependencies=[
                "v0.5 Knowledge Viewer",
                "v0.5.1 Knowledge Viewer Permanent",
                "backend/api/knowledge.py",
                "frontend/app/knowledge/page.tsx",
            ],
            metrics=[
                "PoC 中の /api/knowledge 系成功率 99%以上",
                "PoC ログ上の p95 レスポンス < 1.0 秒",
                "Knowledge Viewer UI の致命的 JS エラー 0 件",
            ],
            owner="Backend Core / Knowledge Viewer",
            documentationLink="docs/operations/v0_5_1_poc_report.md",
            prLink=None,
            development_details="v0.5.1 恒久仕様を前提に、Knowledge Viewer の応答性能と安定性を PoC で計測する。結果は docs/operations/v0_5_1_poc_report.md に集約する。",
            parent_id=None,
        )

        session.commit()
    finally:
        session.close()


def main() -> None:
    upsert_backend_items()
    upsert_db_items()


if __name__ == "__main__":
    main()

