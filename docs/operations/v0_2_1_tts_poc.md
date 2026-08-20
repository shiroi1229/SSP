# v0.2.1 TTS Quality PoC

## 目的
- v0.2で動いているTTS Managerをv0.2.1でより本番耐性のある品質まで引き上げる。
- レイテンシ・成功率・重大エラー率といった自動指標に加え、主観評価で「瑞希の声らしさ」も確認する。

## 対象コンポーネント
- `modules/tts_manager.py`（キャッシュ・フォールバック・タイムアウトの堅牢化）
- `backend/api/tts.py`（latency/error_code/fallback を含むレスポンス）
- `/api/tts` へのリクエストログ（SessionLog）

## シナリオ
1. **速報セリフ**（短文・speaker=1）
2. **長文セリフ**（speaker=2, emotion=angry）
3. **感情込み**（speaker=1, emotion=joy）
4. **Voicevox応答なし**（Voicevox を停止した状態で500ms間隔で5回送信）
5. **キャッシュ再利用**（同じ text＋emotion で再度送信して音声キャッシュが使われるか確認）

## 観測指標
| 指標 | 収集方法 | 目標 |
| --- | --- | --- |
| 平均TTSレイテンシ | `/api/tts` 応答に含まれる `tts_latency_ms` の平均 | 1500ms 以下 |
| TTS成功率 | ステータス 2xx の割合 | 95%以上 |
| 重大TTSエラー率 | `error_code` に `tts_timeout`/`tts_voicevox_error`/`tts_unknown_error` を含む件数の割合 | 1%未満 |
| キャッシュヒット率 | 同一 text+emotion のリクエストで `fallback_used` が false で `audio_path` が再利用されていればヒットとカウント | 60%以上 |
| 主観評価 | 長文/感情セリフを人間が 1〜5 評価 | 3 以上 |

## 実施フロー
1. PoC用のテストデータを `tools/v0_2_1_tts_scenario` （これから作る）で流す。
2. `/api/tts` から返る `tts_latency_ms` / `fallback_used` / `error_code` を CSV にまとめる。
3. 感情ごとに音声ファイルを聞き、聞き取りやすさ・感情の自然さを記録。
4. `docs/operations/v0_2_1_tts_poc_report.md` に結果を記入し、改善余地のある組み合わせ（例: `angry` で latency > 2s）を一覧化する。

## 合格基準
- PoC対象の各シナリオで目標指標を満たすか（または改善案を残す）。
- 重大エラー発生時に `fallback_used` が true になり、HTTP 503 + `error_code` で原因がわかる。
- キャッシュヒット率を PoC 実行中に 60%以上となるよう調整。
- `tts_debug` UI から各シナリオが再生でき、レイテンシ・Status が表示される。
