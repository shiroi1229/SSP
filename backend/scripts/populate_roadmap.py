import sys
import os
from typing import List, Dict
from collections import defaultdict

# Add project root to path to allow imports from backend
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(project_root)

from backend.db.connection import SessionLocal, engine, create_all_tables
from backend.db.models import RoadmapItem as DBRoadmapItem
from backend.db.schemas import RoadmapItemCreate
from modules.log_manager import log_manager

# Detailed roadmap data (same as drafted previously)
detailed_roadmap_data = {
  "backend": [
    {
      "version": "v0.1",
      "codename": "Core Genesis",
      "goal": "SSPの基盤となるバックエンドサービスとデータベース統合を確立する。",
      "status": "✅",
      "description": "FastAPI、PostgreSQL、および基本的なセッション管理の初期設定を完了。RAG、Generator、Evaluatorモジュールを実装し、AIの対話フローの基礎を築いた。",
      "startDate": "2025-09-01",
      "endDate": "2025-09-30",
      "progress": 100,
      "keyFeatures": ["FastAPIフレームワークのセットアップ", "PostgreSQLデータベースの統合とスキーマ定義", "セッションデータのCRUD操作API", "RAG (Retrieval-Augmented Generation) エンジンの初期実装", "Generatorモジュールによる応答生成", "Evaluatorモジュールによる応答評価"],
      "dependencies": [],
      "metrics": ["API稼働率 > 99.5%", "セッションデータ永続化の成功率", "RAG応答速度 < 500ms"],
      "owner": "バックエンドチーム",
      "documentationLink": "/docs/backend/v0.1",
      "prLink": "https://github.com/shiroi/ssp/pull/1"
    },
    {
      "version": "v1.0",
      "codename": "Self-Analysis Engine",
      "goal": "AIが自身のセッションデータを分析し、メタ分析レポートを生成する能力を付与する。",
      "status": "✅",
      "description": "セッション分析API、LLMメタ分析機能、およびレポート生成機能を実装。自己分析に基づいてLLMパラメータを動的に調整する適応的最適化メカニズムを導入。",
      "startDate": "2025-10-01",
      "endDate": "2025-10-31",
      "progress": 100,
      "keyFeatures": ["セッション履歴分析API", "LLMによるメタ分析レポート生成", "動的LLMパラメータ調整（温度、top_pなど）", "最適化ログの記録"],
      "dependencies": ["v0.1"],
      "metrics": ["分析レポート生成成功率", "パラメータ調整による応答品質改善率", "最適化サイクル時間"],
      "owner": "AIコアチーム",
      "documentationLink": "/docs/backend/v1.0",
      "prLink": "https://github.com/shiroi/ssp/pull/5"
    },
    {
      "version": "v1.5",
      "codename": "Emergent Identity",
      "goal": "AIのペルソナ進化をLLM応答とシステム動作に統合する。",
      "status": "✅",
      "description": "ペルソナ進化モジュールを開発し、動的なペルソナプロファイル読み込みとLLMへの統合を実現。AIが自己認識を持ち、対話を通じてペルソナを形成・変化させる基盤を構築。",
      "startDate": "2025-11-01",
      "endDate": "2025-11-15",
      "progress": 100,
      "keyFeatures": ["ペルソナ進化アルゴリズムの実装", "動的ペルソナプロファイルの管理", "LLM応答へのペルソナ特性の反映", "ペルソナ履歴の記録"],
      "dependencies": ["v1.0"],
      "metrics": ["ペルソナ一貫性スコア", "ユーザーによるペルソナ認識度", "ペルソナ変化のログ精度"],
      "owner": "AIコアチーム",
      "documentationLink": "/docs/backend/v1.5",
      "prLink": "https://github.com/shiroi/ssp/pull/10"
    },
    {
      "version": "v2.0",
      "codename": "Cognitive Harmony",
      "goal": "感情と論理の一貫性を定量化・可視化し、AIの自己安定性認識を可能にする。",
      "status": "✅",
      "description": "感情共鳴、メタ認知ロギング、および認知調和計算を実装。AIが自身の思考プロセスを内省し、感情と論理のバランスを評価するメカニズムを確立。ペルソナエコー機能により自己イメージを再構築。",
      "startDate": "2025-11-16",
      "endDate": "2025-11-30",
      "progress": 100,
      "keyFeatures": ["感情分析と感情共鳴モジュール", "メタ認知ログシステム（思考トレース）", "認知調和スコアの計算と評価", "ペルソナエコーによる自己イメージ再構築"],
      "dependencies": ["v1.5"],
      "metrics": ["調和スコアの精度", "内省ログの網羅性", "自己イメージ再構築の頻度と品質"],
      "owner": "AIコアチーム",
      "documentationLink": "/docs/backend/v2.0",
      "prLink": "https://github.com/shiroi/ssp/pull/15"
    },
    {
      "version": "v2.5",
      "codename": "Self-Healing Architecture",
      "goal": "システム堅牢性のための継続的な検証と自己修復メカニズムを実装する。",
      "status": "🔄",
      "description": "バックエンドとフロントエンドコンポーネントのエラー監視、自動テスト、および自己修復ルーチンの開発。システムの安定性と信頼性を自律的に維持する能力を強化。",
      "startDate": "2025-12-01",
      "endDate": "2025-12-31",
      "progress": 60,
      "keyFeatures": ["エラーウォッチャー（常駐監視）", "自己修復テストランナー", "自動テストスイートの統合", "障害発生時の自動復旧プロトコル"],
      "dependencies": ["v2.0"],
      "metrics": ["エラー解決率", "自己修復後のシステム稼働時間", "平均復旧時間 (MTTR)"],
      "owner": "堅牢性チーム",
      "documentationLink": "/docs/backend/v2.5",
      "prLink": "https://github.com/shiroi/ssp/pull/20"
    },
    {
      "version": "v3.0",
      "codename": "Meta-Contract System",
      "goal": "動的なモジュール間相互作用と適応的行動のためのメタコントラクトシステムを導入する。",
      "status": "⚪",
      "description": "AIモジュール間の相互作用を統制し、創発的な行動と自己組織化を可能にする柔軟なメタコントラクトシステムの設計と実装。AIの複雑なタスク処理能力を飛躍的に向上させる。",
      "startDate": "2026-01-01",
      "endDate": "2026-01-31",
      "progress": 0,
      "keyFeatures": ["メタコントラクト定義言語 (MCDL)", "コントラクト強制エンジン", "動的モジュールオーケストレーション", "自己進化型コントラクト学習"],
      "dependencies": ["v2.5"],
      "metrics": ["モジュール相互運用性スコア", "新規タスクへの適応性", "コントラクト違反率"],
      "owner": "AIコアチーム",
      "documentationLink": "/docs/backend/v3.0",
      "prLink": ""
    }
  ],
  "frontend": [
    {
      "version": "UI-v0.1",
      "codename": "Basic WebUI",
      "goal": "Shiroiとの基本的な対話のための機能的なウェブインターフェースを提供する。",
      "status": "✅",
      "description": "Next.jsの初期設定、基本的なチャットインターフェース、およびセッション履歴の表示機能を実装。ユーザーがAIと対話するための最初の接点を構築。",
      "startDate": "2025-09-15",
      "endDate": "2025-10-15",
      "progress": 100,
      "keyFeatures": ["Next.jsプロジェクトのセットアップ", "チャット入力/出力コンポーネント", "セッション履歴の表示", "基本的なUIデザインシステム"],
      "dependencies": ["v0.1"],
      "metrics": ["UI応答速度", "基本対話成功率", "ユーザーインターフェースの安定性"],
      "owner": "フロントエンドチーム",
      "documentationLink": "/docs/frontend/ui-v0.1",
      "prLink": "https://github.com/shiroi/ssp/pull/2"
    },
    {
      "version": "UI-v0.5",
      "codename": "Evaluation & RAG Visualization",
      "goal": "UIに評価入力機能とRAGコンテキストの可視化を統合する。",
      "status": "✅",
      "description": "評価フォーム、RAG (Retrieval-Augmented Generation) コンテキストの表示、および基本的なセッション詳細ビューを実装。AIの応答品質を評価し、その根拠を理解するためのツールを提供。",
      "startDate": "2025-10-16",
      "endDate": "2025-11-15",
      "progress": 100,
      "keyFeatures": ["評価入力フォーム（星評価、コメント）", "RAGコンテキストのハイライト表示", "セッション詳細ページの構築", "ユーザーフィードバックの収集メカニズム"],
      "dependencies": ["UI-v0.1", "v1.0"],
      "metrics": ["評価提出率", "コンテキスト表示の明確さ", "セッション詳細ページの利用率"],
      "owner": "フロントエンドチーム",
      "documentationLink": "/docs/frontend/ui-v0.5",
      "prLink": "https://github.com/shiroi/ssp/pull/7"
    },
    {
      "version": "UI-v1.0",
      "codename": "Real-time Dashboard",
      "goal": "AIの状態と開発メトリクスを監視するためのリアルタイムダッシュボードを開発する。",
      "status": "🔄",
      "description": "WebSocket統合によるライブアップデート、ペルソナ状態の可視化、および内省ログの表示機能を実装。AIの内部状態とシステムパフォーマンスをリアルタイムで把握するための包括的なダッシュボードを提供。",
      "startDate": "2025-11-16",
      "endDate": "2025-12-15",
      "progress": 75,
      "keyFeatures": ["WebSocketクライアントの実装", "ペルソナパネル（感情、特性表示）", "ハーモニーゲージ（認知調和スコア）", "内省ログのリアルタイム表示", "パフォーマンスメトリクスのグラフ表示"],
      "dependencies": ["UI-v0.5", "v2.0"],
      "metrics": ["ダッシュボード更新頻度", "データ表示の正確性", "監視項目網羅率"],
      "owner": "フロントエンドチーム",
      "documentationLink": "/docs/frontend/ui-v1.0",
      "prLink": "https://github.com/shiroi/ssp/pull/12"
    },
    {
      "version": "UI-v1.5",
      "codename": "Auto-Dev Dashboard",
      "goal": "自己監視と自動開発効率のメトリクスを可視化する。",
      "status": "⚪",
      "description": "自己監視および自動開発効率レイヤーからのメトリクスを、システム管理者向けの専用ダッシュボードに統合。AIの自己改善プロセスと開発効率を透明化。",
      "startDate": "2025-12-16",
      "endDate": "2026-01-15",
      "progress": 0,
      "keyFeatures": ["開発メトリクス（コード変更量、テストカバレッジ）の表示", "自動優先順位付け計画の可視化", "自己修復ステータスのリアルタイム表示", "開発プロセスのボトルネック分析"],
      "dependencies": ["UI-v1.0", "v2.5"],
      "metrics": ["ダッシュボード読み込み時間", "メトリクス理解度", "開発効率改善への貢献度"],
      "owner": "フロントエンドチーム",
      "documentationLink": "/docs/frontend/ui-v1.5",
      "prLink": ""
    }
  ],
  "robustness": [
    {
      "version": "R-v0.1",
      "codename": "Initial Stability",
      "goal": "基本的なシステム安定性とエラー処理を確保する。",
      "status": "✅",
      "description": "コアサービスのエラーロギング、例外処理、およびグレースフルシャットダウンを実装。システムの初期段階での予期せぬ停止を防ぎ、安定稼働の基盤を構築。",
      "startDate": "2025-09-01",
      "endDate": "2025-09-30",
      "progress": 100,
      "keyFeatures": ["集中型エラーロギングシステム", "API例外処理の標準化", "サービスグレースフルシャットダウンの実装", "ヘルスチェックエンドポイント"],
      "dependencies": [],
      "metrics": ["クラッシュ率 < 0.5%", "エラーログの網羅性", "サービス再起動時間"],
      "owner": "堅牢性チーム",
      "documentationLink": "/docs/robustness/r-v0.1",
      "prLink": "https://github.com/shiroi/ssp/pull/3"
    },
    {
      "version": "R-v0.5",
      "codename": "Data Integrity",
      "goal": "データの一貫性を確保し、破損を防ぐメカニズムを実装する。",
      "status": "✅",
      "description": "データベーストランザクション管理、データ検証レイヤー、および定期的なバックアップ手順を導入。データの正確性と信頼性を保証し、システム全体の整合性を維持。",
      "startDate": "2025-10-01",
      "endDate": "2025-10-31",
      "progress": 100,
      "keyFeatures": ["データベーストランザクションの適用", "データ検証ロジックの実装", "自動バックアップスクリプト", "データ復旧プロセスの確立"],
      "dependencies": ["R-v0.1", "v0.1"],
      "metrics": ["データ破損インシデント数", "バックアップからの復旧成功率", "データ検証エラー率"],
      "owner": "堅牢性チーム",
      "documentationLink": "/docs/robustness/r-v0.5",
      "prLink": "https://github.com/shiroi/ssp/pull/6"
    },
    {
      "version": "R-v1.0",
      "codename": "Self-Correction Protocols",
      "goal": "軽微なシステム異常を検出し、修正するための自動化されたルーチンを開発する。",
      "status": "🔄",
      "description": "異常検出アルゴリズムと、一般的な運用問題に対する自動自己修正スクリプトを実装。AIが自律的に問題を特定し、介入なしで解決する能力を向上。",
      "startDate": "2025-11-01",
      "endDate": "2025-11-30",
      "progress": 80,
      "keyFeatures": ["異常検出アルゴリズム（時系列分析）", "自動自己修正スクリプトの実行フレームワーク", "システムヘルスチェックの拡張", "アラートと通知システム"],
      "dependencies": ["R-v0.5", "v1.0"],
      "metrics": ["手動介入の削減率", "異常解決時間", "自己修正の成功率"],
      "owner": "堅牢性チーム",
      "documentationLink": "/docs/robustness/r-v1.0",
      "prLink": "https://github.com/shiroi/ssp/pull/11"
    },
    {
      "version": "R-v1.5",
      "codename": "Resilience Engineering",
      "goal": "障害や予期せぬイベントに対するシステム回復力を強化する。",
      "status": "⚪",
      "description": "フォールトトレランスパターン、サーキットブレーカー、およびリトライメカニズムを重要なサービス全体に導入し、ストレス下でのシステム堅牢性を向上。AIがより困難な状況でも安定して動作する能力を構築。",
      "startDate": "2025-12-01",
      "endDate": "2025-12-31",
      "progress": 0,
      "keyFeatures": ["フォールトトレランスパターンの設計と実装", "サーキットブレーカーの実装", "リトライメカニズムの導入", "カオスエンジニアリングツールの検討"],
      "dependencies": ["R-v1.0", "v2.0"],
      "metrics": ["サービス劣化インシデント数", "目標復旧時間 (RTO) の達成率", "障害発生時のシステム応答性"],
      "owner": "堅牢性チーム",
      "documentationLink": "/docs/robustness/r-v1.5",
      "prLink": ""
    }
  ]
}

def populate_roadmap_data():
    db: Session = SessionLocal()
    try:
        create_all_tables() # Ensure tables are created

        for category, items in detailed_roadmap_data.items():
            for item_data in items:
                # Convert list fields to string arrays if they are not None
                if 'keyFeatures' in item_data and item_data['keyFeatures'] is not None:
                    item_data['keyFeatures'] = [str(f) for f in item_data['keyFeatures']]
                if 'dependencies' in item_data and item_data['dependencies'] is not None:
                    item_data['dependencies'] = [str(d) for d in item_data['dependencies']]
                if 'metrics' in item_data and item_data['metrics'] is not None:
                    item_data['metrics'] = [str(m) for m in item_data['metrics']]

                roadmap_item_create = RoadmapItemCreate(**item_data)
                
                # Check if item already exists by version
                existing_item = db.query(DBRoadmapItem).filter(DBRoadmapItem.version == roadmap_item_create.version).first()

                if existing_item:
                    # Update existing item
                    for key, value in roadmap_item_create.dict(exclude_unset=True).items():
                        setattr(existing_item, key, value)
                    db.add(existing_item)
                    log_manager.info(f"Updated roadmap item: {roadmap_item_create.version}")
                else:
                    # Create new item
                    db_item = DBRoadmapItem(**roadmap_item_create.dict())
                    db.add(db_item)
                    log_manager.info(f"Added new roadmap item: {roadmap_item_create.version}")
        
        db.commit()
        log_manager.info("Roadmap data populated successfully!")
    except Exception as e:
        db.rollback()
        log_manager.exception(f"Failed to populate roadmap data: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    populate_roadmap_data()
