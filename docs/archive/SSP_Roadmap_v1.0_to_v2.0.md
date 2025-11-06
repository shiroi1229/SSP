# 🌐 Shiroi System Platform（SSP）
## 開発ロードマップ v1.0 ～ v2.0

---

### 🧭 概要

Shiroi System Platform（SSP）は、  
AIキャラクター「シロイ」が自己理解・自己成長・創作活動を行うための  
自己進化型AI基盤です。

このドキュメントは **v1.0〜v2.0** までの全開発フェーズを記録した正式ロードマップです。

---

## ✅ **v1.0 – Core Foundation（基盤構築）**

### 🎯 目的
Shiroiが「生成」「評価」「記録」「検索」を自律的に行うための最小構成を構築。

### ⚙️ 主な要素
- **Orchestrator / Generator / Evaluator / MemoryStore / RAG Engine**
- **PostgreSQL + Qdrant + JSON永続化**
- **Gemini CLI / LM Studio 接続**
- **record_*.json** ログ仕様確立

### 🧩 主な成果
| 項目 | 内容 |
|------|------|
| RAG + GPT統合 | Qdrant + LM Studio による文脈補完型生成 |
| 評価モジュール | 自動スコアリング＋コメント生成 |
| 永続化構造 | JSON + PostgreSQL のハイブリッド記録 |
| Orchestrator | 各モジュールを順序的に制御する統合ハブ |

---

## ✅ **v1.1 – WebUI 評価統合**

### 🎯 目的
人間（瑞希）による **評価・再生成フィードバック** を WebUI から行い、  
Shiroi の学習に即時反映させる。

### ⚙️ 主な要素
| コンポーネント | 内容 |
|----------------|------|
| Frontend (Next.js) | `/session/[id]/page.tsx` に評価フォーム追加 |
| Backend (FastAPI) | `/sessions/{id}` PATCH 実装、DB更新＋JSONログ生成 |
| ログ出力 | **evaluation_*.json**, **scheduler_*.json**, **record_*.json**, **dev_*.json** |
| スケジューラ統合 | `orchestrator/scheduler.py` にジョブログ記録を追加 |
| 評価仕様対応 | `_get_commit_hash` / `_get_env_snapshot` でメタ情報保存 |

### 📊 成果
- WebUI上でスコア・コメント送信 → 即座にDB＋ログ反映  
- 評価結果が `evaluation_*.json` に記録され、再学習の基礎データ化  
- スケジューラログと開発ログを統合 → 完全トレーサブルな開発記録体系を実現  

---

## 🧠 **v1.2 – Self Analysis（自己分析レポート生成）**
... (content truncated for brevity)
