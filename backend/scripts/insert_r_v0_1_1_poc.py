import contextlib
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(project_root)

from backend.db.connection import SessionLocal
from backend.db.models import RoadmapItem


def main() -> None:
    with contextlib.closing(SessionLocal()) as session:
        existing = session.query(RoadmapItem).filter_by(version="R-v0.1.1_PoC").first()
        if existing:
            print("R-v0.1.1_PoC already exists; skipping insert.")
            return

        parent = session.query(RoadmapItem).filter_by(version="R-v0.1").first()
        parent_id = parent.id if parent else None

        item = RoadmapItem(
            version="R-v0.1.1_PoC",
            codename="Core Stability PoC",
            goal=(
                "R-v0.1で定義した「Core Stability Framework」が、本番運用レベルの障害（"
                "プロセスクラッシュ・一時的なDB/Redis障害・設定不整合）が発生しても自己復旧し続けるかを検証するPoCフェーズ。"
                "実運用に近いシナリオで連続稼働させ、「止まりにくさ」「復旧の早さ」「ログ欠損の少なさ」を定量的に測定し、"
                "恒久仕様に向けてボトルネックと改善点を洗い出す。"
            ),
            status="⚪",
            description=(
                "R-v0.1.1_PoCは、R-v0.1の安定基盤を「理論上できている」から「現場で壊れにくい」状態まで引き上げるための検証フェーズ。"
                "意図的にAPI例外・外部サービス停止・設定ミスを注入し、Retry / Logger / ConfigLoader / Supervisor が期待通りに連携するかを確認する。"
            ),
            startDate="2025-02-25",
            endDate="2025-03-05",
            progress=0,
            keyFeatures=[
                (
                    "docs/operations/r_v0_1_1_poc_plan.md — R-v0.1の安定性を検証するためのPoC計画書。本番を想定した障害シナリオ・評価指標・合格ラインを文章で定義する。"
                ),
                (
                    "backend/tests/test_r_v0_1_resilience_poc.py — RetryManager / Logger / ConfigLoader / Supervisor を対象にした自動テスト。"
                    "プロセスクラッシュや例外発生時に、再起動とログ保存が期待どおり行われるかを検証する。"
                ),
                (
                    "tools/r_v0_1_failure_injector.py — 意図的に例外・タイムアウト・外部サービス停止を発生させる失敗注入ツール。"
                    "R-v0.1のモジュール群に対してカオス的な負荷をかけるためのCLI。"
                ),
                (
                    "tools/r_v0_1_supervisor_stress_runner.py — Supervisorとバックエンドを一定時間連続稼働させ、繰り返しクラッシュ/再起動を行うストレステスト用ランナー。"
                    "連続稼働時間と再起動回数を記録する。"
                ),
                (
                    "frontend/app/analysis/r_v0_1_resilience/page.tsx — R-v0.1.1_PoCの結果を可視化する分析画面。再起動回数・平均復旧時間・ログ欠損率などをグラフとテーブルで表示する。"
                ),
                (
                    "docs/operations/r_v0_1_1_poc_report.md — PoC実行後に結果をまとめるレポート。観測された指標と改善提案を恒久仕様に反映するためのドキュメント。"
                ),
            ],
            dependencies=[
                (
                    "バックエンド: FastAPI / Supervisor / pytest / asyncio"
                ),
                (
                    "DB: PostgreSQL・域ｰｸ邯壹せ繝医い縺ｫ蠕後ｧ九↓險倬鹸縺ｫ蜃ｺ蜉帙ョessure test中のエラー/復旧ログを蓄積。"
                ),
                (
                    "Infra: Redis・医せ繝・・繧ｿ繧ｹ蝣ｱ蜻翫・蜀崎ｵｷ蜍輔ヨ繝ｪ繧ｬ繝ｼ縲∫ocker Compose・医し繝ｼ繝薙せ隧ｳ邯壼喧縺ｫ讀懃ｴ｢縺励◆"
                ),
            ],
            metrics=[
                "連続稼働時間 竕･ 24h以上（致命的な停止なし）",
                "障害発生から自動復旧完了までの平均時間 竕､ 30秒以内",
                "ログ欠損率（致命的エラー時に失われたログ割合） 竕､ 1%未満",
                "手動介入が必要になった障害件数 竕､ 0〜ごく少数",
            ],
            owner="Backend Core / Reliability Engineer / SRE",
            documentationLink=None,
            prLink=None,
            development_details=(
                "R-v0.1で実装されたRetryManager・Logger・ConfigLoader・Supervisorを対象に、現実的な障害シナリオをまとめて検証する。"
                "PoCでは、tools配下の失敗注入ツールとSupervisorストレスランナーを用いて、クラッシュ・タイムアウト・外部サービス停止・設定不整合などを計画的に発生させる。"
                "検証の流れとしては、(1) r_v0_1_1_poc_plan.mdで定義したシナリオをもとにテスト環境を構築し、"
                "(2) backend/tests/test_r_v0_1_resilience_poc.pyで基本挙動を自動テストし、"
                "(3) toolsスクリプトで長時間の連続稼働と障害注入を行い、"
                "(4) frontend/app/analysis/r_v0_1_resilience/page.tsxで指標を可視化・評価する、という形を想定している。"
                "得られた指標（平均復旧時間・再起動回数・ログ欠損率・手動介入頻度）が合格ラインを満たした場合、"
                "その設定値や運用ルールを「恒久仕様」としてR-v0.1にフィードバックし、以降のR系（R-v0.2以降）はこの土台の上で設計・評価を進める。"
            ),
            parent_id=parent_id,
        )
        session.add(item)
        session.commit()
        print("Inserted R-v0.1.1_PoC roadmap item.")


if __name__ == "__main__":
    main()
