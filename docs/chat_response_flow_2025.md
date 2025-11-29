# チャット応答ロジック詳細（2025年11月時点）

---

## 1. ユーザー入力
- ユーザーが「こんにちは」と送信。

---

## 2. `run_workflow("こんにちは")` 呼び出し
- orchestrator/workflow.py の `run_workflow` が呼ばれる。

---

## 3. ContextManager 初期化
- `ContextManager`インスタンス生成。
- `short_term.user_input` に「こんにちは」をセット。
- `short_term.timestamp` に現在時刻をセット。

---

## 4. RAG（検索型文脈拡張）実行
- `_run_rag_engine(context_manager)` 実行。
  - `RAGEngine.get_context("こんにちは")` を呼ぶ。
    1. 「こんにちは」を埋め込みベクトル化。
    2. Qdrantで類似知識IDを検索。
    3. PostgreSQLから該当IDのテキスト（知識）を取得。
    4. 取得できれば整形して `context` 文字列を作成、できなければ `"情報不足"`。
  - `short_term.context` に文脈（例: "[1] (world_knowledge)\nこんにちはは挨拶です" など）が格納。

---

## 5. 応答生成（Generator）実行
- `_run_generator(context_manager)` 実行。
  - `short_term.user_input`（「こんにちは」）と `short_term.context`（RAG文脈）を取得。
  - `generate_response(model, context, prompt)` を呼ぶ。
    1. `prompts/gemini_instruction.txt`（キャラ指示等）を読み込む。
    2. system prompt: 指示文＋「出力は日本語で、キャラクター 'シロイ' の一人称口調で回答してください。」
    3. user content: チャット履歴（mid_term.chat_history、通常は空）＋
       ```
       user: 質問: こんにちは

       参考情報:
       [RAGで得たcontext]
       ```
    4. LLM（analyze_text）を呼び出し、system prompt＋user contentで応答生成。
    5. 生成結果をクリーニングし、`mid_term.generated_output` に格納。

---

## 6. 応答パース・評価
- `_run_parser_and_evaluator(context_manager)` 実行。
  - `short_term.generator_response`（生成応答）と `short_term.context` を取得。
  - 必要に応じてJSONパース（LM Studio用分岐、現状は通常テキスト）。
  - `short_term.final_output` に応答を格納。
  - `evaluate_output(answer, context)` を呼び、応答の質をLLMで評価（世界観整合性・具体性・文体一貫性）。
  - スコアやフィードバックを `short_term.feedback` に格納。

---

## 7. ログ・DB保存
- `MemoryStore.save_record_to_db(log_data)` でやりとりをDB保存。
- `logs/session_YYYYMMDD_...json` にも保存。

---

## 8. フロントエンドへの返却
- `run_workflow` の戻り値（`log_data`）として、`final_output`（応答テキスト）、`feedback`（評価スコア等）が返る。

---

## 9. まとめ：実際の回答例

- RAGで「こんにちは」に関連する知識が見つかれば、その内容を参考にLLMが「こんにちは！今日も元気だよ。何かお手伝いできることはある？」のようなキャラ口調で返答。
- 知識がなければ「こんにちはは挨拶です」などの一般知識や、キャラの自己紹介的な返答になることも。

---

## 10. 分岐・例外

- RAGや生成でエラーが出た場合は、エラー内容が context に記録され、応答も「Error: ...」となる。
- 評価スコアが低くても自動再生成はされないが、外部から再生成をトリガー可能。

---

### 【要点まとめ】

- 「こんにちは」→RAGで知識検索→文脈＋履歴＋指示でLLM応答→評価→返却
- すべての処理はContextManagerで多層的に管理
- 異常時はエラー応答、履歴・評価・最適化ログも全て記録

---

この流れが**現状の「こんにちは」発言に対する回答ロジックの全体像**です。
