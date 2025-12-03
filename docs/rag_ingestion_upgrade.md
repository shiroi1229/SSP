# RAG インジェスト基盤アップグレード計画

## 1. 目的
- 手動インプットされた知識をプロダクション品質の RAG データとして即座に活用できるようにする。
- チャンク分割・正規化・ベクトル化・投入処理をサービス層として分離し、可観測性と再現性を確保する。
- Qdrant と PostgreSQL の整合性を維持しつつ、将来のスケールアウトや自動要約にも対応できる構造を用意する。

## 2. システム構成概要
1. **KnowledgeIngestionService (新規)**
   - FastAPI `POST /api/knowledge` から呼び出されるファサード。
   - 入力バリデーション、ジョブ発行、ステータス管理を担当。
2. **Preprocessor**
   - HTML 除去、Unicode 正規化、言語判定、メタデータ補完。
   - 依存ライブラリ: `beautifulsoup4`, `unicodedata`, `langdetect` 等。
3. **Chunker**
   - `tiktoken` ベースでトークン長を制御。最大 512〜768 tokens を目安にチャンク生成。
   - セクションタイトルや自動要約を付与して `metadata` に含める。
4. **EmbeddingService**
   - `sentence-transformers` でローカル埋め込み (例: `all-MiniLM-L12-v2`)。
   - オプションで外部 API (OpenAI, VertexAI) へ切り替え可能なアダプタ設計。
5. **VectorStoreClient**
   - Qdrant へのバルク upsert & リトライをラップ。
   - `qdrant-client` の `upsert` に対して非同期投入、DLQ (Postgres テーブル) へ失敗記録。
6. **Persistence Layer**
   - `knowledge_documents` / `knowledge_chunks` に原文・チャンク・要約を保存。
   - Qdrant payload と同期できる `chunk_id` をキーとして管理。
7. **Background Worker**
   - RQ / Celery / Dramatiq いずれか。最小構成なら FastAPI + `BackgroundTasks` で開始し、将来的に専用ワーカーへ移行可能。
8. **Monitoring**
   - Prometheus exporter で `ingestion_latency`, `chunk_count`, `embedding_failures` などを計測。
   - ログは `modules.log_manager` 経由で構造化 JSON ログ化。

## 3. 処理フロー
1. フロントエンド (`RagDashboard`) から `POST /api/knowledge`。
2. FastAPI 層が `KnowledgeIngestionService` に処理依頼。
3. Preprocessor がテキスト正規化 → Chunker が分割。
4. EmbeddingService がチャンクごとにベクトル生成。
5. VectorStoreClient が Qdrant へバルク upsert、結果を記録。
6. Postgres へ `knowledge_documents` (原文) / `knowledge_chunks` (チャンク + メタ) を書き込み。
7. 失敗したチャンクは DLQ テーブルで再処理キューイング。
8. 完了後ステータスを返却し、フロントはポーリングで進捗表示可能。

## 4. 技術スタック / 依存ライブラリ
| 分類 | 候補ライブラリ | 備考 |
| --- | --- | --- |
| 正規化 / HTML 除去 | `beautifulsoup4`, `ftfy` | HTML タグ・制御文字除去 |
| 言語判定 | `langdetect`, `fasttext` | 多言語サポート時に利用 |
| トークナイザ | `tiktoken`, `nltk` | OpenAI モデル互換トークン数計測 |
| 埋め込み | `sentence-transformers`, `transformers`, OpenAI API | 切替できるようアダプタ化 |
| ワーカー | `rq`, `celery`, `dramatiq` | 最初は FastAPI `BackgroundTasks` でも可 |
| モニタリング | `prometheus-client`, `opentelemetry` | メトリクス/トレース導入 |

## 5. 実装ロードマップ
1. **Phase 1: サービス分割 + チャンク/埋め込み**
   - `services/knowledge_ingestion_service.py` を新設。
   - Preprocessor / Chunker / EmbeddingService / VectorStoreClient を modules 以下に配置。
   - 既存 `KnowledgeService.add_entry` は新サービスを呼ぶよう移行。
2. **Phase 2: 非同期化 & 監視**
   - RQ などを導入し、投入ジョブをバックグラウンド実行。
   - `/api/knowledge/status/{job_id}` を追加し、UI で進捗確認。
   - Prometheus エンドポイントにインジェストメトリクスを追加。
3. **Phase 3: 高度化 (任意)**
   - 自動要約・タグ付け (例: LLM でエンリッチメント)。
   - 品質スコアリングや重複検出。
   - 再同期 CLI (`python -m backend.scripts.rag_resync`) を用意し、Postgres → Qdrant を再構築可能に。

## 6. テスト戦略
- 単体テスト: Preprocessor / Chunker / EmbeddingService はモック済み依存でテスト。
- API テスト: `POST /api/knowledge` がチャンク生成・Qdrant 呼び出しを行うかを pytest + httpx で確認。
- E2E: サンプルデータを投入し、チャット推論から新規ナレッジが参照されることを確認。

## 7. 今後の課題
- Embedding モデルのホスティング (GPU / CPU) とキャッシング戦略。
- マルチテナント化に備えたコレクション分割。
- セキュリティ (入力フィルタ、アクセス制御) の強化。
