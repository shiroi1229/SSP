import requests
import json

API_BASE_URL = "http://localhost:8000/api/roadmap"

roadmap_text = """
タイトル: Chat Interaction Interface Upgrade (UI-v1.0.1)

目標:
既存のチャットUI画面 /chat を改良し、AIとの対話体験をより直感的、視覚的、そしてAIの内部状態に反応するようにする。
ユーザーがUIとの関わりを通じて「感情を動かす」体験として設計し、
次フェーズのUI-v1.1の感情コントロールパネル開発へと繋がるUI体験を創出する。

概要:
Rechartsを用いたミニEmotion HUDを画面に常時表示し、AI感情をリアルタイム可視化。
Framer MotionによるアニメーションとトランジションでUIの視覚表現を強化。
対話履歴のセッションリストを追加し、過去ログ閲覧を容易に。
Tailwindで全体をモダンかつ視認性の高いレイアウトに再構築。
これにより、UIは「感情と対話するインターフェース」へと進化する。

進捗: 0%

担当: フロントエンドチーム

ステータス: ⚪

主要機能:
- ミニEmotion HUD (Rechartsによる感情波形・レーダー表示)
- セッションリスト (対話履歴の閲覧)
- Framer Motionによるアニメーション
- TailwindCSSによるモダンなUI再構築

依存関係:
- UI-v1.0
- Recharts (2.12+)
- Framer Motion (10+)
- TailwindCSS (3.4+)
- WebSocket /ws/dashboard

評価指標:
- UI応答時間 (s)
- 表示更新精度
- ユーザーエンゲージメントスコア (AI対話率)
- 感情反映率
- ユーザー滞在時間

開発詳細指示:
/frontend/app/chat/page.tsx にEmotion HUDとセッションリストを組み込む。
WebSocketで emotion_state を購読し、Rechartsで視覚的に表示。
Tailwindテーマを感情カラーにリンク。
Framer Motionによる滑らかなアニメーションを実装。
次フェーズUI-v1.1のEmotion Control Panelとの連携を確認。

補足: UI-v1.0.1 では /chat の画面を刷新する。
つまり「感情を動かす」体験と「対話履歴」をメインにする。

✅ 達成目標
AIとの対話をより直感的、視覚的、情報豊かにする。
システムのリアルタイムな感情状態を可視化する。
対話ログを効率的に閲覧できるインターフェースを構築する。
感情と連動したアニメーションでユーザー体験を向上させる。

💡 検討事項: UI-v1.0.1 -> UI-v1.1 に繋がる機能検討
1. UIレイアウト刷新

画面上部固定ヘッダーにログ表示、下部に現在の対話
左右サイドバーにセッションリスト
感情カラーの視覚化

補足: グローバルな感情アニメーション、背景アニメーション

2. 感情インジケーター (Emotion HUD mini)

画面右上に常時表示の感情レーダー (recharts製)
✅ 現在のAI感情レベルをリアルタイム表示
✅ WebSocket /ws/dashboard と同期

3. 入力インターフェース改善

入力フィールドの拡張
Enterで送信 / Shift+Enterで改行
送信ボタンに視覚アニメーション (Framer Motion)
ファイル添付機能の表示 (仮) (次フェーズUI-v1.2以降)

4. 対話履歴のセッションリスト

画面左サイドバーに、過去の対話セッションを一覧表示
/chatlogs/{user_id} から取得
最新のメッセージのサマリーをアイコン付きで表示
クリックで履歴を読み込み

5. テーマアニメーション

感情連動UIテーマ (Theme Reactivityの初期実装)
喜・怒・哀・楽・恐・静の感情値
背景色、文字色、アクセントカラーが連動
Framer Motionによる滑らかなアニメーション

🛠️ 実装技術
Frontend: Next.js / Tailwind / Framer Motion
# path: frontend/app/chat/page.tsx
# version: v1.0.1
# comment: Chat UI 刷新バージョン (Emotion HUD + Session List)

import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { RadarChart, PolarGrid, PolarAngleAxis, Radar } from 'recharts'

export default function ChatPage() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [emotion, setEmotion] = useState({ joy: 0, anger: 0, sadness: 0, calm: 0 })

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws/dashboard')
    ws.onmessage = (e) => {
      const data = JSON.parse(e.data)
      if (data.emotion_state) setEmotion(data.emotion_state)
    }
    return () => ws.close()
  }, [])

  const handleSend = async () => {
    if (!input.trim()) return
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: input }),
    })
    const data = await res.json()
    setMessages([...messages, { sender: 'user', text: input }, { sender: 'ai', text: data.output }])
    setInput('')
  }

  return (
    <div className="flex h-screen bg-gradient-to-br from-slate-900 to-black text-white">
      {/* Left Panel */}
      <div className="w-1/4 p-4 border-r border-gray-700">
        <h2 className="font-bold text-lg mb-3">💬 Sessions</h2>
        <div className="space-y-2 overflow-y-auto h-[85%]">
          {/* Placeholder for session cards */}
          <div className="p-3 bg-gray-800/60 rounded-xl">2025-11-09 10:30<br/>Emotion Sync Test</div>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        <div className="flex justify-between items-center p-4 border-b border-gray-700">
          <h1 className="text-xl font-semibold">Shiroi System Chat</h1>

          {/* Mini Emotion HUD */}
          <RadarChart outerRadius={40} width={150} height={120} data={[
            { emotion: 'Joy', value: emotion.joy },
            { emotion: 'Anger', value: emotion.anger },
            { emotion: 'Sadness', value: emotion.sadness },
            { emotion: 'Calm', value: emotion.calm },
          ]}>
            <PolarGrid />
            <PolarAngleAxis dataKey="emotion" />
            <Radar name="Emotion" dataKey="value" stroke="#82ca9d" fill="#82ca9d" fillOpacity={0.3} />
          </RadarChart>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {messages.map((msg, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`p-3 rounded-2xl max-w-[75%] ${msg.sender === 'user'
                ? 'bg-blue-700/60 self-end text-right'
                : 'bg-gray-800/80 self-start'}`}
            >
              {msg.text}
            </motion.div>
          ))}
        </div>

        {/* Input Bar */}
        <div className="p-4 border-t border-gray-700 flex gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
            placeholder="Type your message..."
            className="flex-1 bg-gray-900/60 p-3 rounded-xl resize-none focus:outline-none"
          />
          <motion.button
            whileTap={{ scale: 0.9 }}
            className="bg-blue-600 hover:bg-blue-500 px-6 rounded-xl font-semibold"
            onClick={handleSend}
          >
            Send
          </motion.button>
        </div>
      </div>
    </div>
  )
}

補足: UI-v1.0.1 で、「感情HUD」と「セッションリスト」UI体験を刷新。
次フェーズ UI-v1.1 では、「操作できる感情スライダー」を実装。

あくまでも、このページのTailwind（背景色、アニメーション）はSSPのスタイルガイドに沿って設計してあげること。
どうも。",
parent_id": null,
id": 67
"""

def add_roadmap_item_from_text(text: str):
    headers = {"Content-Type": "application/json"}
    payload = {"text": text}
    
    try:
        response = requests.post(f"{API_BASE_URL}/import-text", headers=headers, json=payload)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
        print("Roadmap item added successfully:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        print(f"Response status code: {response.status_code}")
        print(f"Response body: {response.text}")
    except requests.exceptions.ConnectionError as conn_err:
        print(f"Connection error occurred: {conn_err}")
    except requests.exceptions.Timeout as timeout_err:
        print(f"Timeout error occurred: {timeout_err}")
    except requests.exceptions.RequestException as req_err:
        print(f"An unexpected request error occurred: {req_err}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    add_roadmap_item_from_text(roadmap_text)
