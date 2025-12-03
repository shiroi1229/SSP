"""
Add a roadmap item 'v2.2.1 Chat Feedback Loop Refinement' to the database using the RoadmapItem model.

Usage:
  python backend/scripts/add_feedback_loop_refinement_v2_2_1.py

This script opens a DB session via SessionLocal and upserts a roadmap item by
`version`. It is intentionally conservative: it only inserts if not exists,
or updates a defined set of fields if present.

After running this, run:
  python -m backend.scripts.roadmap_doc_sync
to regenerate `docs/roadmap/*.json`.
"""

from typing import Optional
import sys
import os

# Ensure project root (one level above `backend`) is on sys.path so `backend` is importable
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(project_root))

from backend.db.connection import SessionLocal
from backend.db.models import RoadmapItem


DATA = {
    "version": "v2.2.1",
    "codename": "Chat Feedback Loop Refinement",
    "goal": "GeneratorとEvaluatorの自己採点付きフィードバックループを、実運用に耐える形でシンプルかつ安定したチャット体験に仕立て直す。",
    "status": "planned",
    "startDate": "2025-09-24",
    "endDate": "2025-10-01",
    "progress": 0,
    "description": (
        "v2.2.1では、v2.2 Multi-Module Optimization で導入した Adaptive Feedback Loop を、"
        "実際のチャット体験に最適化するフェーズとして位置づける。これまでの SSP は、"
        "Generator と Evaluator を 1 ターンごとに二重呼び出しし、自分の回答を LLM 自身に採点させる"
        "という実験的な構造を持っていたが、その評価結果は主にログ用途に留まり、"
        "ユーザー体験との結びつきが弱かった。本フェーズでは、\n"
        "・どのような観点でスコアが低いときに再生成を許可するか（世界観整合性 / 具体性 / 文体一貫性）、\n"
        "・再生成を何回まで許可するか（max_retries の設計）、\n"
        "・RAG コンテキストがノイズになるケースをどう扱うか、\n"
        "・英語のメタ文など、評価用プロンプトに由来する“人間には不要なテキスト”をどこで除去するか、\n"
        "といったルールを明示的なポリシーとして定義し、FeedbackLoop 内部の分岐と ContextManager のキー設計に落とし込む。"
        "これにより、自己採点は「無限ループする実験機構」ではなく、「1回または少数回の再生成を制御する安全なゲート」として振る舞う。"
    ),
    "keyFeatures": [
        "orchestrator/feedback_loop_integration.py: 評価スコアに基づく再生成ポリシーを明文化し、score >= 0.7 なら即採用、閾値未満かつポリシーが許す場合のみ 1 回再生成するロジックに統一。max_retries のデフォルト値と、RecoveryPolicyManager からの上書きルールを整理し、FeedbackLoop 全体の終了条件を明示する。",
        "modules/generator.py: _clean_llm_output() による英語メタ文の除去を正式な仕様として位置付け、「If not relevant, disregard them.」など評価・ガイダンス由来のメッセージを final_output から排除。system_prompt / persona_prompt / user_content の役割を明確にし、ユーザーに見せるテキストと内部制御用テキストを分離する。",
        "modules/evaluator.py: evaluate_output() で返される JSON 評価（worldview_consistency, specificity, style_consistency, rating）を、FeedbackLoop の再生成ポリシーに直接渡す形に整理。fallback_evaluation_data の扱いを見直し、「評価に失敗した場合はスコア 0 とするか／現行値を保持するか」をポリシーとして定義する。",
        "orchestrator/workflow/runtime.py: run_context_evolution_cycle() から見たときに、FeedbackLoop が『1ターン内で最大何回の LLM 呼び出しを行うか』が明示的にわかるよう、ログメッセージと異常検知（InsightMonitor.detect_anomaly）の連携を整理。再生成が連続した場合でも snapshot / rollback との整合性が崩れないよう、スナップショット ID の扱いを統一する。",
        "docs/chat_response_flow_2025.md: 「こんにちは」発話時の処理フローを v3 時代の実装（CompositeRagEngine + ContextManager + Adaptive Feedback Loop）に合わせて全面更新し、短期 / 中期 / 長期コンテキストのキー、RAG コンテキストのフォーマット、Generator / Evaluator / FeedbackLoop の責務境界をドキュメントとして固定化する。",
    ],
    "dependencies": [
        "v2.2（Multi-Module Optimization）; orchestrator/workflow/runtime.py; modules/generator.py; modules/evaluator.py; modules/rag/engine.py; modules/llm.py。",
    ],
    "metrics": [
        "チャット応答の平均レイテンシを v2.2 比で +10% 以内に維持しつつ、評価スコア（rating）の中央値を 0.05 以上向上させる。",
        "英語メタ文や内部ガイダンス文がユーザー UI に漏れる事例を 0 件にする（ログベースで検証）。",
        "低スコアによる再生成が発生したターンのうち、2 回以上の再生成が必要な割合を 5% 未満に抑える。",
        "FeedbackLoop / ContextManager 周辺の異常検知（InsightMonitor.detect_anomaly）が、1 セッションあたり平均 0.05 件以下で安定していること。",
    ],
    "owner": "Orchestrator / Generator / Evaluator",
    "documentationLink": "",
    "prLink": "",
    "development_details": (
        "実装面では、まず現行の logs/context_history.json を解析し、mid_term.generated_output・"
        "mid_term.evaluation_score・long_term.optimization_log など、FeedbackLoop 由来のキーがどのように遷移しているかをトレースする。"
        "そのうえで、modules/generator.py に _clean_llm_output() を導入し、過去ログで観測された英語メタ文（例: "
        "\"If not relevant, disregard them.\", \"Feel free to disregard them if they are not relevant.\" など）を"
        "ホワイトリスト方式で削除する。これは、後続の Evaluator や UI が『ユーザーに見せるべき最終テキスト』だけを扱えるようにするための前処理である。\n\n"
        "FeedbackLoop 側では、score >= 0.7 を基本閾値としつつ、RecoveryPolicyManager から返されるポリシーに応じて "
        "max_retries を調整する仕組みを整理する。具体的には、InsightMonitor.detect_anomaly() が『出力のばらつきが大きい』"
        "などの異常を検出した場合、再生成を 1 回だけ許可するか、スナップショットに即座にロールバックするかをポリシーで決定する。\n\n"
        "また、evaluate_output() の JSON パースロジックと fallback の設計を見直し、「評価 JSON が壊れている場合に"
        "安易に 0.0 スコアを返してしまうと、FeedbackLoop が過度に再生成を試みる」という問題を避ける。"
        "そのために、fallback_evaluation_data の rating を固定値ではなく、『評価失敗』を示す特殊値として扱い、"
        "Policy 側で『評価が失敗した場合は現行出力を受け入れる』といった分岐を定義する。\n\n"
        "最後に、docs/chat_response_flow_2025.md を現在のコード（orchestrator/workflow/runtime.py・"
        "orchestrator/feedback_loop_integration.py・modules/rag/engine.py・modules/llm.py）と同期させる。"
        "これにより、瑞希や開発者が「こんにちは」と入力した際に、短期コンテキストのどのキーに何が入り、"
        "RAG コンテキストがどのようなフォーマットで LLM に渡され、Generator と Evaluator が何回 LLM を呼び出し、"
        "FeedbackLoop がどの条件で終了するかを、コードと同じ粒度で追跡できるようにする。"
    ),
    "interaction_notes": None,
    "parent_id": None,
}


def upsert_roadmap_item(session, version: str, data: dict) -> Optional[RoadmapItem]:
    existing = session.query(RoadmapItem).filter(RoadmapItem.version == version).one_or_none()
    if existing:
        print(f"Found existing roadmap item with version={version}, updating fields.")
        existing.codename = data.get("codename", existing.codename)
        existing.goal = data.get("goal", existing.goal)
        existing.status = data.get("status", existing.status)
        existing.startDate = data.get("startDate", existing.startDate)
        existing.endDate = data.get("endDate", existing.endDate)
        existing.progress = data.get("progress", existing.progress)
        existing.description = data.get("description", existing.description)
        existing.keyFeatures = data.get("keyFeatures", existing.keyFeatures)
        existing.dependencies = data.get("dependencies", existing.dependencies)
        existing.metrics = data.get("metrics", existing.metrics)
        existing.owner = data.get("owner", existing.owner)
        existing.documentationLink = data.get("documentationLink", existing.documentationLink)
        existing.prLink = data.get("prLink", existing.prLink)
        existing.development_details = data.get("development_details", existing.development_details)
        existing.interaction_notes = data.get("interaction_notes", existing.interaction_notes)
        existing.parent_id = data.get("parent_id", existing.parent_id)
        session.add(existing)
        session.commit()
        return existing

    print(f"Creating new roadmap item with version={version}.")
    item = RoadmapItem(
        version=data.get("version"),
        codename=data.get("codename"),
        goal=data.get("goal"),
        status=data.get("status"),
        startDate=data.get("startDate"),
        endDate=data.get("endDate"),
        progress=data.get("progress", 0),
        description=data.get("description"),
        keyFeatures=data.get("keyFeatures", []),
        dependencies=data.get("dependencies", []),
        metrics=data.get("metrics", []),
        owner=data.get("owner"),
        documentationLink=data.get("documentationLink"),
        prLink=data.get("prLink"),
        development_details=data.get("development_details"),
        interaction_notes=data.get("interaction_notes"),
        parent_id=data.get("parent_id"),
    )
    session.add(item)
    session.commit()
    return item


def main() -> None:
    session = SessionLocal()
    try:
        item = upsert_roadmap_item(session, DATA["version"], DATA)
        if item:
            print("Roadmap item upserted:", item)
        else:
            print("No item created/updated.")
    except Exception as exc:  # pragma: no cover - CLI utility
        print("Error while upserting roadmap item:", exc)
    finally:
        session.close()


if __name__ == "__main__":
    main()

