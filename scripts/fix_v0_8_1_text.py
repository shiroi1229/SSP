# path: scripts/fix_v0_8_1_text.py
# version: v0.1
# purpose: Repair v0.8.1 roadmap text in DB so doc sync reflects correct Japanese strings

# -*- coding: utf-8 -*-
"""
Fix mojibake text for v0.8.1 / v0.8.1_PoC RoadmapItem entries.

This script updates the roadmap_items rows in the DB and then you should
run backend.scripts.roadmap_doc_sync to regenerate docs/roadmap JSON files.
"""

from __future__ import annotations

import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.append(project_root)

from backend.db.connection import SessionLocal  # type: ignore
from backend.db.models import RoadmapItem  # type: ignore


def update_v0_8_1(session) -> None:
    item = session.query(RoadmapItem).filter(RoadmapItem.version == "v0.8.1").first()
    if not item:
        return

    item.goal = (
        "v0.8 で構築した Emotion Engine / Stage UI を本番運用レベルに引き上げる。"
        "TTS / Live2D / OSC のいずれかに障害が起きてもステージが止まらず、"
        "emotion → tts → osc → result のログトレースを常に追える状態にする。"
    )
    item.status = "✅"
    item.description = (
        "v0.8 では「AI が演じる」ための土台（Emotion Engine / Stage UI）が揃ったが、"
        "長時間稼働・障害注入・負荷変動といった現実的なステージ条件ではまだ壊れやすい。\n"
        "v0.8.1 では TTS / Live2D / OSC の失敗やタイムアウトを health_summary として検知し、"
        "StageDirector が run を継続しながら degraded 状態をフラグとして残せるようにする。\n"
        "各 run ごとに emotion / tts / osc / result のログを揃えて保存し、"
        "「どの感情がどんな演出と結果につながったか」を後から追跡できるようにする。"
    )
    item.keyFeatures = [
        "modules/emotion_engine.py — 長時間稼働を想定した感情ベクトル生成とログ強化。",
        "modules/tts_manager.py — 再試行・タイムアウト制御付きの TTS 実行と health_summary 連携。",
        "modules/osc_bridge.py — Live2D / VTS への OSC 送信のリトライと障害検知。",
        "modules/stage_director.py — emotion / tts / osc / result を束ねた health snapshot を生成し、WebSocket にストリーミングする。",
        "backend/api/stage_controller.py — /api/stage/health でステージ状態と degraded 回数を取得できるようにする。",
    ]
    item.metrics = [
        "障害注入シナリオ込みで Stage run success rate 95%以上。",
        "各 run で emotion / tts / osc / result のいずれかが欠けるケースを 0 件にする（log trace completeness 100%）。",
        "/api/stage/health の health snapshot 生成〜配信の p95 レイテンシ < 500ms。",
    ]
    item.development_details = (
        "EmotionEngine で算出した感情ベクトルを TTSManager / OSCBridge 経由で StageDirector に集約し、"
        "各ステージ run ごとに health_snapshot として JSON へまとめる。TTS / OSC のタイムアウトや例外は "
        "asyncio.wait_for + try/except で検知し、degraded フラグとエラー内容を health_summary に残す。\n"
        "StageDirector は WebSocket を通じて progress / health をフロントエンドへストリーミングし、"
        "frontend/app/stage/page.tsx から run ごとの状態を追えるようにする。"
        "バックエンド側では /api/stage/health で最新の stage_status / degraded_events を取得できる。"
    )


def update_v0_8_1_poc(session) -> None:
    item = (
        session.query(RoadmapItem)
        .filter(RoadmapItem.version == "v0.8.1_PoC")
        .first()
    )
    if not item:
        return

    item.goal = (
        "v0.8 と v0.8.1 の構成で Emotion Engine / Stage UI が、"
        "本番想定の負荷・長時間稼働・障害条件のもとでも KPI を満たせるかを PoC で検証する。"
    )
    # まだ PoC をやりきっていない前提で、進行中ステータスにしておく
    if item.progress and item.progress >= 100:
        item.status = "✅"
    else:
        item.status = "⏳"
    item.description = (
        "StageDirector / TTSManager / OSCBridge / Stage UI を使って failure injection 付きのステージ再生を自動実行し、"
        "成功率・degraded 発生頻度・ログトレース欠損・レイテンシをまとめて評価する。\n"
        "tools/v0_8_1_stage_poc_runner.py で JSONL ログを出力し、"
        "docs/operations/v0_8_1_poc_report.md に集計結果と考察を残す。"
    )
    item.keyFeatures = [
        "docs/operations/v0_8_1_poc_plan.md — PoC のシナリオと評価観点を定義する。",
        "tools/v0_8_1_stage_poc_runner.py — Stage UI / Emotion Engine に対し failure injection 付きの連続再生を自動実行し、結果を JSONL に記録する。",
        "docs/operations/v0_8_1_poc_report.md — success rate / degraded / log trace completeness などを集計し、v0.8.1 恒久仕様の KPI 達成状況をまとめる。",
    ]
    item.metrics = [
        "PoC シナリオにおける Stage run success rate 95%以上。",
        "各 run あたりの degraded 発生回数 < 1.0。",
        "emotion / tts / osc / result のログ欠損率 0%（log trace completeness 100%）。",
    ]
    # development_details は既存の英語テキストが有用なのでそのまま残す


def main() -> None:
    session = SessionLocal()
    try:
        update_v0_8_1(session)
        update_v0_8_1_poc(session)
        session.commit()
    finally:
        session.close()


if __name__ == "__main__":
    main()
