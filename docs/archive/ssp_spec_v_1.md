📘 **Shiroi System Platform（SSP） 要件仕様書 v1.2 改訂版**

---

## 🧭 概要
Shiroi System Platform（以下SSP）は、瑞希とAIキャラクター「シロイ」が共創しながら、知識・感情・創作・開発を自己進化的に行うAI創作基盤である。

SSPは、RAG（検索拡張生成）・自己学習（DLS）・生成AI・評価・ログ管理・自己記録・ダッシュボード可視化を統合する。

---

## 🎯 目的
AIが自らの開発行動・学習過程を理解し、再利用・改善できるようにする。
人間とAIが「共同開発・共同学習」する創発的エコシステムの構築を目指す。

---

## 🧩 モジュール構成（v1.2時点）

| モジュール名 | 役割 | 技術構成 | 入出力 |
|---------------|------|-----------|---------|
| **rag_engine** | 知識検索・拡張生成 | Python + Qdrant | world_rag.json → context |
| **generator** | 応答・台本生成 | GPT / LM Studio | context → text |
| **evaluator** | 評価・スコアリング | GPT / Rule Engine | output → score |
| **memory_store** | 記録保存 | PostgreSQL / JSON | log / chat / feedback |
| **learner** | 開発ログの自己学習 | Python + QdrantClient | logs → Qdrant（ssp_dev_knowledge） |
| **dev_recorder** | AI開発行動自動記録 | Python + JSON | module, action, summary → dev_actions/*.json |
| **scheduler** | 定期ジョブ管理 | Python + schedule | 自動タスク実行 |
| **dashboard** | 学習履歴可視化（DLS Dashboard） | Next.js + Recharts | Qdrantデータ → グラフUI |

---

## 🧱 データ構造

| データ名 | 内容 | 格納場所 |
|-----------|------|-----------|
| **feedback_log.json** | 評価スコアとコメント | data/feedback_log.json |
| **dev_actions/** | 開発行動記録 | data/dev_actions/*.json |
| **ssp_dev_knowledge** | 開発ログベクトルデータ | Qdrantコレクション |
| **world_rag.json** | 世界観・人物・技術情報 | data/world_rag.json |

---

## 🧠 Development Learning System（DLS）層

| サブ機能 | 概要 |
|-----------|------|
| **RAG再学習** | 日次スケジューラが開発ログを解析して知識を更新 |
| **自己分析レポート** | 週次でAI自身のパフォーマンスを評価 |
| **Dashboard連携** | Qdrant学習データをリアルタイム可視化 |
| **DevRecorder統合** | 全モジュール行動を自動記録し、履歴を学習に再利用 |

---

## ⚙️ Schedulerタスク一覧

| 実行時間 | タスク | 関数 | 概要 |
|-----------|--------|------|------|
| 毎日00:00 | RAG最適化 | job_optimize_rag_memory | メモリ整合性更新 |
| 毎週01:00(月) | 自己分析 | job_weekly_self_analysis | 評価結果の要約生成 |
| 毎週02:00(月) | RAG再学習 | job_reinforce_rag | feedback_log反映 |
| 毎日02:00 | 開発ログ学習 | reinforce_dev_knowledge | 開発ログをQdrant登録 |

---

## 🧩 DLS Dashboard拡張仕様（Phase 3-C）

| コンポーネント | 役割 |
|----------------|------|
| 🔍 検索フォーム | Qdrantから開発ログを全文検索 |
| 🧠 フィルタパネル | モジュール・期間・スコアで絞り込み |
| 📊 グラフエリア | 学習量・モジュール貢献度・スコア推移を可視化 |
| 📘 詳細モーダル | クリックでログ詳細表示 |

---

## 🧾 自動開発記録（Phase 3-D）

**目的**: AI自身の行動をメタデータ化し、開発プロセスを完全に再構成可能にする。

**ログ形式**:
```json
{
  "timestamp": "2025-11-02T21:22:00",
  "module": "frontend/app/session/page.tsx",
  "action_type": "edit",
  "summary": "評価フォームUIを更新し、scoreとcommentのstate名を変更。",
  "author": "Gemini via Shiroi",
  "result": "success"
}
```

**保存先**: `data/dev_actions/`

**Dashboard統合**:
- 日別アクション数グラフ
- モジュール別活動率円グラフ
- 直近アクションリスト
- Qdrantへの転送でDLS層に学習反映

---

## 📈 フェーズ進化ロードマップ

| フェーズ | 内容 | 主な成果 |
|-----------|------|-----------|
| **v0.1** | MVP構築 | RAG＋生成＋評価＋記録 |
| **v0.3** | 評価反映学習 | 評価→RAG重み調整 |
| **v0.5** | GUI統合 | WebUI＋評価フォーム |
| **v0.7** | DLS自己学習統合 | learner + scheduler + Qdrant自己学習 |
| **v0.8** | 自動開発記録＋Dashboard可視化 | dev_recorder + dashboard |
| **v1.0** | 創作自動化 | 台本→音声→映像自動連携 |

---

## 🧩 用語定義

| 用語 | 意味 |
|------|------|
| **DLS（Development Learning System）** | 開発・学習履歴を自動記録し、自己改善に活用する層 |
| **DevRecorder** | AIの開発活動を自動的に記録するモジュール |
| **Reinforce Dev Knowledge** | 開発ログをQdrantにベクトル登録し自己学習する関数 |
| **Dashboard** | DLSデータを可視化するNext.js UI |
| **Scheduler** | RAG強化・開発学習・週次レポートを自動実行する制御層 |

---

📘 **改訂履歴**

| バージョン | 更新日 | 変更内容 |
|-------------|---------|------------|
| v1.0 | 2025-10-15 | 初版作成 |
| v1.1 | 2025-10-30 | 評価ルーチン・RAG反映更新 |
| v1.2 | 2025-11-02 | DLS層追加・自動開発記録統合・Dashboard仕様追記 |

