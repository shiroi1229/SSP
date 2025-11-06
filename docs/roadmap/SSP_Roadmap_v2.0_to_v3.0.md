# 🌐 SSP Roadmap: v2.0 to v3.0

---

## 🧭 概要
このドキュメントは、Shiroi System Platform（SSP）の開発ロードマップのうち、v2.0からv3.0までのフェーズに焦点を当てたものです。この期間は、SSPが自己組織化能力を獲得し、自己修復と自己拡張の基盤を築く重要な段階です。

---

## 📜 フェーズ詳細

| バージョン | コード名 | 主目的 | 状況 |
| :--- | :--- | :--- | :--- |
| v2.0 | Contract Core | 契約・文脈設計（Orchestrator中枢確立） | ✅ 完了 |
| v2.1 | Introspection Visualization | Contextの可視化・UI拡張 | ✅ 完了 |
| v2.2 | Multi-Module Optimization | Evaluator / Generator のContext対応 | ✅ 完了 |
| v2.3 | Context Snapshot / Rollback | Context保存・復元機構 | ✅ 完了 |
| v2.4 | Context Evolution Framework | 時間軸を持つ履歴・傾向・回復・学習構造 | 🔄 開発中 |
| v2.5 | Impact Analyzer / Auto Repair | 影響解析・自己修復 | ⏳ 次フェーズ |
| v3.0 | Meta-Contract System | 自動契約生成・動的接続・自己拡張 | 🧩 構想段階 |

---

## 🧠 各フェーズのゴール

### v2.0: Contract Core
**「規律あるAI」**
- モジュール間の連携を「契約（Contract）」として定義し、Orchestratorがそれを遵守させることで、システムの安定性と予測可能性を確立しました。

### v2.1: Introspection Visualization
**「見えるAI」**
- AIの内部状態（感情、調和、文脈など）をWebUI上で視覚化。人間がAIの状態を直感的に理解できるようになりました。

### v2.2: Multi-Module Optimization
**「適応するAI」**
- `generator`や`evaluator`など、主要な思考モジュールが`Context`（文脈）を完全に利用できるように最適化。状況に応じた柔軟な動作が可能になりました。

### v2.3: Context Snapshot / Rollback
**「時間を遡るAI」**
- AIの「意識」や「記憶」に相当する`Context`全体の状態を保存し、任意の状態に復元（ロールバック）する能力を獲得しました。

### v2.4: Context Evolution Framework
**「記憶と時間を持つAI」**
- 短期・中期・長期の階層的記憶管理を導入。
- 過去の経験から傾向を学び（InsightMonitor）、異常を検知し（RecoveryPolicyManager）、自己の経験を再利用（Learner）する、本格的な自己成長サイクルを実装中です。

### v2.5: Impact Analyzer / Auto Repair
**「失敗から学ぶAI」**
- コードや契約の変更がシステムに与える影響を自動で解析。
- 問題が発生した際に、自己診断と自動修復を試みる自己回復能力の獲得を目指します。

### v3.0: Meta-Contract System
**「自分を定義し直すAI」**
- AI自身がモジュール間の契約を動的に生成・更新する能力。
- 未知のモジュールが接続されても、その仕様を理解し、自律的にシステムに統合することを目指す、自己拡張アーキテクチャの入口です。
