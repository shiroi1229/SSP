# Codex Agent Guide for This Repo

このリポジトリで作業する Codex / GPT へのガイドラインです。
特にロードマップまわりの扱いを明示しておきます。

## ロードマップのソース・オブ・トゥルース

- **唯一のソース・オブ・トゥルース**: PostgreSQL の `roadmap_items` テーブル  
  - モデル: `backend.db.models.RoadmapItem`
  - セッション: `backend.db.connection.SessionLocal`

ロードマップの進捗・ステータス・説明文を変更するときは、必ず **DB を更新** すること。

### 禁止事項（直接編集しない）

次のファイルは **生成物／スナップショット** 扱いなので、直接編集しないこと:

- `docs/roadmap/system_roadmap.json`
- `docs/roadmap/system_roadmap_extended.json`
- `roadmap_dump.json`
- `frontend/.next/**` 内のロードマップ関連ファイル

これらを手で書き換えても、後で同期スクリプトが走ると **DB の内容で上書きされる** ため、
人間ユーザーが見ている状態と Codex が書き換えた状態がズレてしまいます。

### 正しい更新ルート

1. **DB を更新する**
   - Python から直接:
     - `SessionLocal()` でセッションを開き、`RoadmapItem` を更新して `commit()` する。
   - もしくは FastAPI 経由:
     - `/api/roadmap/...` エンドポイントを使って更新する。

2. **ドキュメント JSON を再生成する**
   - コマンド:  
     `python -m backend.scripts.roadmap_doc_sync`
   - これにより:
     - `docs/roadmap/system_roadmap.json`
     - `docs/roadmap/system_roadmap_extended.json`
     - `roadmap_dump.json`
     が DB の最新状態から再生成される。

### 解析用ユーティリティ

- `roadmap_dump.json` は解析スクリプト用のダンプ:
  - 例: `analyze_roadmap.py`, `list_robustness.py`, `scripts/roadmap_status.py`
  - 必要であれば `dump_roadmap_to_file.py` から再生成する。
  - **ここを編集しても DB は変わらない** ことに注意。

## 一般方針

- ロードマップの意味的な変更（progress, status, description, development_details など）は、
  **必ず DB 経由で行う**。
- `docs/roadmap/` 配下は「人間・UI用ビュー」、`roadmap_dump.json` は「解析用ダンプ」として扱う。
- どのファイルを触るか迷ったら:
  - 「この変更は最終的にユーザーの見ているロードマップに反映されるべきか？」  
    → Yes なら **DB 更新 + `roadmap_doc_sync`** を選ぶこと。

## エンコードとシェルについて

- **ファイルエンコード前提**
  - Assume all files are UTF-8 encoded.
  - Do not assume cp932 / Shift_JIS. 文字化け対策としても UTF-8 前提で扱うこと。

- **コマンド実行について（この環境固有の注意）**
  - 実行シェルは **PowerShell** になっていることが多い。
    - `&&` ではなくコマンドは分けて実行する（`cmd1; cmd2` も避け、1コマンドずつ）。
    - `sed` や純粋な bash 組み込みは基本使えない前提で、代わりに:
      - ファイル表示: `Get-Content path -TotalCount N` または `cmd /c type path`
      - 検索: `rg PATTERN path -n --no-config` のようにシンプルに使う。
  - `rg` は「マッチなし」で exit code 1 を返すが、これはエラーではないとみなす（Failed と表示されても“対象なし”なだけ）。
  - ツール未インストール由来のエラー（例: `sed` がない）は避けるため、このリポジトリでは **標準で入っている PowerShell / cmd / rg だけ**を使う方針にする。
