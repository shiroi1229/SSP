"""
Add a roadmap item 'v2.2.2 Session Context Window' to the database using the RoadmapItem model.

Usage:
  python backend/scripts/add_session_context_window_v2_2_2.py

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
    "version": "v2.2.2",
    "codename": "Session Context Window",
    "goal": "チャットごとに「最近の会話履歴」を 1,000 トークン以内で保持するセッションコンテキストウィンドウを導入し、ターンをまたいだ文脈を自然に反映できるようにする。",
    "status": "planned",
    "startDate": "2025-10-02",
    "endDate": "2025-10-10",
    "progress": 0,
    "description": (
        "v2.2.2 は、SSP のチャット体験における「文脈の継続性」を強化するフェーズ。"
        "これまでの v2.2 系では、FeedbackLoop 内で mid_term.chat_history を更新していたものの、"
        "各リクエストごとに新しい ContextManager が生成されるため、LLM に渡される履歴は実質的に「そのターン単発」になっていた。"
        "その結果、DB やログには十分な会話履歴が残っているにもかかわらず、"
        "生成側から見ると“毎回ほぼ初対面”のような応答になりがちだった。"
        "v2.2.2 では、ChatGPT などと同様に、セッションごとの messages テーブルから直近 N ターンを取り出し、"
        "トークン上限（デフォルト 1,000。環境変数 CHAT_CONTEXT_TOKEN_LIMIT で変更可能）の範囲でスライディングウィンドウを構築。"
        "それを mid_term.chat_history として ContextManager に事前注入し、Generator が常に「最近の会話＋今回の発話」を見たうえで応答を生成できるようにする。"
        "古いターンはウィンドウ外に落ちるが、必要であれば要約した形で長期記憶（RAG / knowledge）側に引き継ぐことを前提とした設計とする。"
    ),
    "keyFeatures": [
        "backend/api/chat.py: chat_endpoint 内で、DB messages テーブルから対象 session の全メッセージを created_at ASC で取得し、最後尾から逆順に走査してトークン予算 1,000 以内に収まるウィンドウを構築。user/assistant の role と content だけを残した list[dict] を history_for_llm として組み立て、OrchestratorService.run_chat_cycle(user_input, history=history_for_llm) に渡す。",
        "backend/core/orchestrator_service.py: run_chat_cycle のシグネチャを拡張し、history: Optional[list[dict]] を受け取れるようにする。run_context_evolution_cycle(user_input, history=history) をラップし、従来どおり最終回答文字列のみを返す API 契約は維持する。",
        "orchestrator/workflow/core.py: initialize_components(user_input, history=None) で ContextManager を初期化したあと、history があれば mid_term.chat_history として ContextManager にセットする。これにより modules/generator.py の _prepare_history() は DB から復元された最近のターンを元に user content を組み立てるようになる。",
        "orchestrator/workflow/runtime.py: run_context_evolution_cycle(user_input, history=None) のシグネチャに拡張し、initialize_components(user_input, history=history) を呼ぶ形に統一。Context Evolution のフローそのものは v2.2.1 時点の FeedbackLoop 設計を維持する。",
        "modules/config_manager.py / 環境変数: CHAT_CONTEXT_TOKEN_LIMIT を追加し、デフォルト 1000。_build_history_for_llm() 相当の処理で len(text)//4 などの簡易トークン見積もりを使いながら、将来的により正確なトークナイザを導入できるよう拡張余地を残す。",
    ],
    "dependencies": [
        "v2.2.1（Chat Feedback Loop Refinement）; backend/api/chat.py; backend/core/orchestrator_service.py; orchestrator/workflow/core.py; orchestrator/workflow/runtime.py。",
    ],
    "metrics": [
        "同一セッション内で 3ターン以上続く質問に対して、「前の会話に言及した自然な応答」が返る率を手動評価で 80% 以上にする。",
        "CHAT_CONTEXT_TOKEN_LIMIT=1000 設定時、平均応答レイテンシの悪化を v2.2.1 比 +15% 以内に抑える。",
        "ログ分析において、ユーザーからの「さっき言ったことを覚えていない」「急に話が途切れる」といった苦情タグ付きフィードバック数を 30% 以上削減する。",
    ],
    "owner": "Orchestrator / API / Context Manager",
    "documentationLink": "",
    "prLink": "",
    "development_details": (
        "まず backend/api/chat.py に、小さなヘルパー関数 _build_history_for_llm(db, session_id) を追加する。"
        "この関数は対象セッションの messages を created_at ASC で全取得し、末尾（最新）から逆順に走査しながら、"
        "content の長さからざっくりトークン数を見積もってトークン予算を減算していく。予算が尽きたところでループを止め、"
        "逆順に集めたメッセージを再度 reverse して「古い → 新しい」の順にした list[dict(role, content)] を返す。"
        "role は DB の role をそのまま 'assistant' / それ以外を 'user' として正規化する。"
        "次に OrchestratorService.run_chat_cycle に history 引数を追加し、run_context_evolution_cycle(user_input, history=history) に橋渡しする。"
        "orchestrator/workflow/core.initialize_components(user_input, history=None) では、ContextManager を作成したあとで "
        "history があれば context_manager.set('mid_term.chat_history', history, reason='Seed chat history from DB') を呼び出す。"
        "modules/generator.generate_response() は既に mid_term.chat_history を _prepare_history() で行列に変換する設計になっているため、"
        "この変更だけで LLM に渡る user content に「セッションの最近の会話」が含まれるようになる。\n\n"
        "トークン上限は、config_manager.load_environment() から CHAT_CONTEXT_TOKEN_LIMIT を読み、"
        "値が存在しない場合は 1000 を用いる。len(text)//4 程度の簡易近似から始め、必要になれば将来的に正確なトークナイザに置き換える。"
        "この仕組みによって、セッションが長くなっても「最近の数ターン」は常にコンテキストに残り、"
        "古いターンは自然にウィンドウの外へと押し出される。"
        "RAG 側は、引き続き長期的な知識・出来事（Chronicle や world_knowledge）を補完する役割として分担し、"
        "チャット履歴と長期知識が二重に記録されないよう、source やコレクション設計で住み分ける。"
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

