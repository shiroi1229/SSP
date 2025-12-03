# Chat セッション 1ラウンドのシーケンス

## 1. 前提

- フロント: Next.js (`/chat`, `/chat/[id]`)
- バックエンド: FastAPI (`/api/sessions`, `/api/chat`)
- オーケストレータ: `orchestrator/main.py::run_context_evolution_cycle`
- LLM: `modules/llm.py`（Transformers / HTTP）
- 永続化: PostgreSQL (`sessions`, `messages`, `session_logs`), Qdrant

---

## 2. シーケンス（新規セッション→1ラウンド）

### 2.1 `/chat` 初回アクセス

1. ユーザーが `/chat` にアクセス。
2. `frontend/app/chat/page.tsx` の `useEffect` で:
   - `GET /api/sessions` を呼ぶ。
   - `Envelope[data]` → `SessionSummary[]` を取得。
3. セッションが存在する場合:
   - 先頭の `id` に対して `router.replace("/chat/{id}")`。
4. セッションが存在しない場合:
   - `POST /api/sessions` で新規セッション作成。
   - レスポンスの `id` に対して `router.replace("/chat/{id}")`。

### 2.2 `/chat/[id]` での画面初期化

5. `frontend/app/chat/[id]/page.tsx` がマウント。
6. `useChat(initialSessionId)` が呼ばれ、内部で:
   - `refreshSessions()` → `GET /api/sessions` でサイドバー用 `sessions` を取得。
   - `loadSession(initialSessionId)` → `GET /api/sessions/{id}` で `messages` を読み込み。

---

## 3. メッセージ送信〜応答生成

### 3.1 フロント → バックエンド

7. ユーザーが入力欄にメッセージを入力し、送信ボタンを押す。
8. `useChat.sendMessage()` が実行される:
   - 入力テキストを `optimisticUser` として `messages` state に即座に追加。
   - `setInput("")` / `setLoading(true)`。
   - `POST /api/chat` に以下の JSON を送信:

```json
{
  "user_input": "<ユーザー入力>",
  "session_id": "<現在のセッションIDまたはnull>"
}
```

### 3.2 `/api/chat` での処理

9. FastAPI `chat_endpoint` が `ChatRequest` としてリクエストを受け取る。
10. `session_id` の正規化:
    - クエリ/ボディの `session_id` を `_normalize_session_id()` で整形。
11. セッション確保:
    - `_ensure_session(db, session_id)` で:
      - 既存セッションがあれば取得。
      - なければ UUID で新規 `Session` を作成し、`created_at/updated_at/last_activity_at` をセット。
12. ユーザーメッセージ保存:
    - `DBMessage` として `messages` テーブルに `role="user"` のメッセージを INSERT。
    - `session.last_activity_at` / `updated_at` を更新 → `db.commit()`。

### 3.3 オーケストレータ → LLM

13. `OrchestratorService.run_chat_cycle(user_input)` が呼び出される。
14. `run_context_evolution_cycle(user_input)` で以下を実行:
    - `ContextManager` に `short_term.user_input` として入力を保存。
    - `RAGEngine` を通して Qdrant + Postgres から関連コンテキストを検索し、`rag_context` に保存。
    - `modules/generator` が `modules.llm.analyze_text(rag_context + user_input)` で LLM を呼び出し、一次応答を生成。
    - `modules/evaluator` が LLMに JSON形式の評価を要求し、`evaluation_score` / `evaluation_feedback` を計算（フォールバック付き）。
    - `MemoryStore` が `session_logs` に一連の情報（入力/出力/評価/ワークフロー）を保存。
15. `run_chat_cycle` は、`run_context_evolution_cycle` の結果から最終回答文字列を返す（文字列でない場合は空文字）。

### 3.4 バックエンドでのフォールバック

16. `chat_endpoint` に戻る:
    - `answer` が空文字 or 例外発生時:
      - `_simple_reply(user_input)` で簡易な日本語フォールバックメッセージを生成。
17. アシスタントメッセージ保存:
    - `DBMessage` として `role="assistant"` のメッセージを `messages` に INSERT。
    - `session.last_activity_at` / `updated_at` を更新。
    - タイトルが未設定の場合、`_derive_session_title_from_turn(user_input, answer)` で候補を生成し、`Session.title` にセット。
    - `db.commit()`。

18. セッションサマリログ:
    - `memory_store.save_record_to_db()` が `session_logs` にまとめレコードを保存。

19. レスポンス生成:
    - `ChatTurnPayload(session_id=session.id, message=_message_to_response(assistant_message))` を構築。
    - `Envelope.ok(payload)` を JSON として返す。

---

## 4. 応答のフロント側反映

20. `useChat.sendMessage()` に戻る:
    - レスポンスから `data.session_id` または `data.message.session_id` を取得。
    - `loadSession(returnedSessionId)` で最新のメッセージ履歴を再取得。
    - `refreshSessions(false)` でサイドバーの一覧も更新。
21. タイトルが null の場合:
    - クライアント側で `deriveTitle(user_input)` を実行し、先頭行からタイトルを生成。
    - `PATCH /api/sessions/{id}/title` を呼び出し、タイトルを確定。
    - `sessions` state もタイトル付きに更新。

22. ローディングフラグを `false` に戻し、チャット画面にユーザー＋アシスタントの最新メッセージが表示される。

---

## 5. エラー時のデータフロー

- LLM/オーケストレータエラー:
  - `run_chat_cycle` で例外発生 → `chat_endpoint` でcatch → `_simple_reply` にフォールバック → 200 + フォールバック文。
- DB書き込みエラー（セッションログなど）:
  - `memory_store.save_record_to_db` は try/except 内で呼ばれ、失敗してもチャットレスポンス自体は返す。
- フロント:
  - `/api/chat` が非 2xx を返した場合:
    - `useChat` で `serverError` を設定し、バナー表示＋簡易フォールバックメッセージを会話に追加（必要な場合）。
  - `/api/sessions` 系が失敗した場合:
    - セッションリスト／履歴の読み込みエラーとして、日本語メッセージを UI に表示。

