# タイトル  
Chat: セッション永続化チャット機能の安定化（/api/chat + /api/sessions + LLM連携）

## 概要  
SSP の「AI Chat」機能は、Session/Message モデルと `/api/chat`・`/api/sessions` を使った ChatGPT風のチャットUXを目指しているが、現状は以下の問題により「恒久品質」には達していない。

- DBスキーマと ORM モデルの不整合により、セッションAPIが不安定（`sessions` テーブルが旧仕様のまま）。
- チャットAPIがオーケストレータの破壊的変更に追従できておらず、LLM/AutoRepair 連携で例外が表面化する。
- HTTP LLM + Evaluator が「OpenAI互換＋strict JSON」依存のため、LLMの応答フォーマット揺らぎに弱い。
- フロント側のチャットUI（サイドバー＋/chat/[id]）は設計としては ChatGPT風だが、バックエンドの不安定さにより実運用では沈黙やエラーに繋がるリスクが高い。

この Issue では、チャット機能（バックエンド+フロント）を「恒久品質」で運用可能なレベルに引き上げるための修正をまとめてトラックする。

## 詳細  

### 1. DB スキーマと Session/Message モデルの不整合

**現状**

- `backend/db/models.py` では、チャット用に以下のようなモデルが定義されている。

```python
class Session(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)
    title = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    archived = Column(Boolean, default=False, nullable=False)
    last_activity_at = Column(DateTime(timezone=True), nullable=True, index=True)
    metadata_json = Column(JSON, nullable=True)
```

- しかし実際の PostgreSQL の `sessions` テーブルは、旧仕様のまま：

```sql
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name='sessions';

-- 結果の例
id              integer
timestamp       timestamp with time zone
user_input      text
generated_text  text
rating          integer
feedback        text
```

- これにより `Session` モデルを前提としたクエリ（例: `order_by(Session.created_at)`）が DB 側で `UndefinedColumn` を投げる。

**問題点**

- `/api/sessions` および `/api/chat` は **新しい Session/Message モデル前提**で実装されているが、実DBが旧スキーマのため、以下のリスクがある：
  - セッション一覧の取得 / 詳細取得で `ProgrammingError` が発生し、チャット画面がエラー状態になる。
  - Message テーブルも作成/移行が不完全な可能性があり、履歴永続化が中途半端になっている。

**影響**

- `backend/api/sessions.py` 全般
- `backend/api/chat.py` の Session/Message 操作
- フロントの `/chat`・`/chat/[id]`（セッション一覧と履歴表示）

---

### 2. チャットAPIとオーケストレータの連携崩れ

**現状**

- `backend/core/orchestrator_service.py` の `run_chat_cycle` は `run_context_evolution_cycle(user_input)` をラップする設計。
- チャットAPI (`backend/api/chat.py`) は基本的に OrchestratorService に経由させる設計に寄せているが、過去ログからは以下のようなエラーが確認される：

```text
[Chat] Error: AutoRepairEngine.apply_repair() got an unexpected keyword argument 'target'
[Chat] Error: name 'run_context_evolution_cycle' is not defined
```

**問題点**

- orchestrator 側の実装変更（例: AutoRepairEngine.apply_repair のシグネチャ変更、run_context_evolution_cycle の import/構造変更）に対して、`chat.py` / OrchestratorService が追従しきれていない。
- エラーハンドリングは `_simple_reply` にフォールバックするよう意図されているが、実際には例外がミドルウェアまで伝播して 500 を返すケースもあり得る。

**影響**

- `/api/chat` の信頼性（ユーザー視点で「たまに沈黙する・500になる」原因）。
- ログが大量の Traceback で汚染され、根本原因の切り分けが難しくなる。

---

### 3. LLM/Evaluator のフォーマット依存性

**現状**

- `modules/llm.py` は TRANSFORMERS / HTTP / HYBRID を切り替えられるアダプタとして実装されている。
- HTTP LLM パスは OpenAI互換の `/v1/chat/completions` + `choices[0].message.content` を期待しており、LM Studio 等の設定差分で簡単にフォーマットエラーになる。
- `modules/evaluator.py` は LLM に「純 JSON のみ」を返すことを期待しているが、現実には：
  - ```json ... ``` で囲われたJSON
  - JSON＋自然文の説明
  - そもそも JSON ではない自然文
  など、フォーマットが揺らぐ。

**ログの例**

```text
[Evaluator] Could not extract JSON from LLM response: ...
```

**問題点**

- LLM/HTTPサーバーの設定やモデルを少し変えただけで、Evaluator が頻繁に失敗し、フィードバックループが安定しない。
- いまは JSON抽出のロバスト化が進み始めているが、まだ「フォーマット前提」が色濃く残っており、環境差分に弱い。

**影響**

- 自己評価・メトリクス系の精度・安定性。
- チャット応答は問題なくても、裏側でエラーログが溜まり続けることで運用性が下がる。

---

### 4. フロントエンドチャットUIの状態

**現状**

- `/chat`  
  - `/api/sessions` から既存セッションを取得し、あれば先頭にリダイレクト、なければ `/api/sessions` POST で新規作成して `/chat/{id}` へ遷移。
- `/chat/[id]`  
  - `useChat(initialSessionId)` を使い、  
    - `/api/sessions` → サイドバーに一覧  
    - `/api/sessions/{id}` → メインパネルに履歴  
    - `/api/chat` → 送信＆応答＋Session/Message更新  
  - ChatGPT風の「左にセッション一覧＋右に会話」という UI になっている。
- 一部エラーメッセージやラベルは日本語化・整備されてきているが、まだ英語や過去の文字化けテキストが混在している箇所がある。

**問題点**

- バックエンドの `/api/sessions` / `sessions` スキーマ不整合により、フロント側の正常動作が DB 状態に強く依存しており、環境によってはチャット画面が「準備中のまま」「エラーバナーのみ」となる可能性がある。
- UI テキストの品質が画面ごとにばらついており、「完成したプロダクト」という印象を与えにくい。

---

## 再現手順（例）

1. 現行の PostgreSQL スキーマを持つ環境で backend を起動する。
2. `/api/sessions` にアクセスする、またはフロントで `/chat` 画面を開く。
3. `Session` モデルの `created_at` などを参照するクエリが実行されると、DB が `UndefinedColumn` を投げる。
4. ログに `ProgrammingError: column sessions.created_at does not exist` が記録される。  
   （環境によってはチャット画面がエラー状態になる）

別パスとして:

1. `/api/chat` にユーザー入力を POST。
2. orchestrator 側の実装と `run_context_evolution_cycle` 呼び出しがズレている環境だと、`NameError` や `AutoRepairEngine.apply_repair()` の `TypeError` がログに出る。
3. 例外ハンドリングが不十分な場合、クライアントには 500 が返る。

---

## 修正方針  

### A. DB スキーマの正規化（最優先）

- `backend/db/models.Session` / `Message` と実DBの `sessions` / `messages` テーブルを揃える。
- 具体的には以下いずれか:
  1. 旧 `sessions` テーブルをバックアップ（リネーム）し、新定義どおりに `sessions` / `messages` を再作成（マイグレーションスクリプト化）。  
  2. もしくは ALTER TABLE で `id` を文字列化し、`created_at` / `updated_at` / `archived` / `last_activity_at` 等を追加して徐々に移行。  
     （将来的に旧カラムを削除する計画も含めて設計する）

### B. チャットAPIとオーケストレータ連携の固定化

- `backend/api/chat.py` は基本的に `OrchestratorService.run_chat_cycle` のみを呼ぶように統一し、  
  - 直接 `run_context_evolution_cycle` に依存しないようにする。  
- `run_chat_cycle` 側での例外処理を強化し、  
  - どんな例外でも空文字を返す or 明示的な例外型を投げるように整理。  
- `chat_endpoint` の側では
  - `run_chat_cycle` から空文字 or 例外を受けたら必ず `_simple_reply` でフォールバックし、  
  - HTTP 500 を返さず 200 + 「フォールバックテキスト」を返すように仕様を固定。

### C. LLM/Evaluator のフォーマット耐性向上

- `modules/llm.py`  
  - HTTP パスを環境変数 (`LOCAL_LLM_API_URL`, `LLM_HTTP_CHAT_PATH`, `LLM_HTTP_MODELS_PATH`) で柔軟に調整できる形にして、  
    LM Studio 等のエンドポイント差異に対応しやすくする。  
  - エラー時は JSON で統一したエラー構造（`source_model`, `trend`, `suggestion`）を返し、呼び出し側が「エラーかどうか」を判定しやすくする。
- `modules/evaluator.py`  
  - 既に導入済みの `_extract_json_payload` をベースに、
    - 純 JSON  
    - ```json + JSON```  
    - JSON + 説明文  
    - それ以外（完全に非JSON）  
    の全パターンで「落ちない」ことを保証。  
  - JSON パースに失敗した場合はデフォルト評価（0.0, 短いフィードバック文）で継続するようにする。

### D. フロントチャットUIの仕上げ

- `/chat` / `/chat/[id]` のブートストラップとエラーメッセージを日本語で統一し、  
  - 「セッションを準備しています…」  
  - 「チャットセッションの準備に失敗しました。時間をおいて再度お試しください。」  
  など、ユーザーが状況を理解しやすいメッセージに整理。
- `ChatSessionsSidebar` でのタイトル表示・タイムスタンプ表示を確認し、  
  - タイトルが null の場合のプレースホルダ（例: 「新しいチャット」）  
  - 時刻フォーマットのロケール  
  を揃える。

---

## 影響範囲  

- **バックエンド**
  - `backend/db/models.py`（Session, Message 定義）
  - `backend/db/connection.py`（テーブル作成やマイグレーション補助があれば）
  - `backend/api/sessions.py`（一覧・詳細・作成・更新・タイトル更新）
  - `backend/api/chat.py`（チャット1ターンAPI）
  - `backend/core/orchestrator_service.py`（`run_chat_cycle`）
  - `modules/llm.py`（HTTP LLM 呼び出し・エラー構造）
  - `modules/evaluator.py`（JSONパーサ・fallbackロジック）
- **フロントエンド**
  - `frontend/app/chat/page.tsx`
  - `frontend/app/chat/[id]/page.tsx`
  - `frontend/hooks/useChat.ts`
  - `frontend/components/layout/ChatSessionsSidebar.tsx`
  - `frontend/components/chat/ChatPanel.tsx` 等、チャット表示周り

---

## Acceptance Criteria  

- [ ] `Session` / `Message` モデルと PostgreSQL の `sessions` / `messages` テーブルが一致しており、`/api/sessions` および `/api/sessions/{id}` が例外なく動作する。  
- [ ] `/api/chat` が、オーケストレータ内部でどのような例外が発生しても **HTTP 500 を返さず**、常に 200 + `Envelope[data]` を返し、`data.message.content` にユーザーが読めるテキストが入る。  
- [ ] LLM の応答フォーマット（純JSON/コードフェンス付き/説明付き/非JSON）に関わらず、`modules/evaluator.evaluate_output` が例外を投げずに `evaluation_score` と `evaluation_feedback` を ContextManager に設定する。  
- [ ] `/chat` および `/chat/[id]` にアクセスした際、DB にセッションが存在する環境であれば **必ず** どれかのセッションにリダイレクトされ、履歴が表示される。  
- [ ] タイトル未設定のセッションで最初のユーザーメッセージを送信した場合、適切な自動タイトルが生成され、サイドバーに反映される。  
- [ ] チャット関連のエラーメッセージ（フロント）はすべて UTF-8 の日本語で表示され、文字化けや英語との混在がない。  
- [ ] ログ上、「Evaluator の JSON パース失敗」「/api/chat のオーケストレータ例外」に関するエラー頻度が大幅に減少（事前のベースライン比で 80%以上削減）している。

---

## ラベル案  

- bug
- enhancement
- backend
- frontend
- chat
- robustness
- LLM

