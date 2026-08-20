'use client';

import { useEffect, useMemo, useRef, useState } from 'react';

const INITIAL_MESSAGES = [
  {
    id: 'system-hello',
    role: 'assistant' as const,
    content: 'こんにちは！プロジェクトの進捗や次のステップについて知りたいことがあれば何でも聞いてください。'
  }
];

type Role = 'user' | 'assistant';

type ChatMessage = {
  id: string;
  role: Role;
  content: string;
  animateKey?: string;
};

function formatTime(date: Date) {
  return date.toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit' });
}

function useTypewriter(text: string, animateKey: string) {
  const [visible, setVisible] = useState('');
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    setVisible('');
    setProgress(0);

    if (!text) return;

    const total = text.length;
    const interval = Math.max(12, Math.floor(1200 / Math.max(total, 1)));
    let index = 0;

    const timer = setInterval(() => {
      index += 1;
      setVisible(text.slice(0, index));
      setProgress(Math.min(100, Math.round((index / total) * 100)));

      if (index >= total) {
        clearInterval(timer);
        setVisible(text);
        setProgress(100);
      }
    }, interval);

    return () => clearInterval(timer);
  }, [text, animateKey]);

  return { visible, progress };
}

function MessageBubble({ message }: { message: ChatMessage }) {
  const animateKey = message.animateKey ?? message.id;
  const { visible, progress } = useTypewriter(
    message.role === 'assistant' ? message.content : message.content,
    animateKey
  );

  const showCursor = message.role === 'assistant' && visible.length < message.content.length;
  const timestamp = useMemo(() => formatTime(new Date()), []);

  return (
    <div className={`message-row ${message.role}`}>
      <div className="avatar" aria-hidden>
        {message.role === 'assistant' ? 'AI' : 'You'}
      </div>
      <div className={`message ${message.role}`}>
        <span className="meta">{message.role === 'assistant' ? 'アシスタント' : 'あなた'} ・ {timestamp}</span>
        <span>
          {message.role === 'assistant' ? visible : message.content}
          {showCursor && <span className="typing-cursor" aria-hidden />}<br />
        </span>
        {message.role === 'assistant' && (
          <div className="progress-bar" aria-label="typing progress">
            <span style={{ width: `${progress}%` }} />
          </div>
        )}
      </div>
    </div>
  );
}

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>(INITIAL_MESSAGES);
  const [input, setInput] = useState('');
  const [pending, setPending] = useState(false);
  const listRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim()) return;
    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: input.trim()
    };

    setMessages((prev) => [...prev, userMessage]);
    setPending(true);
    setInput('');

    // Mock response for now. Integrate your API call here if available.
    const mockResponse =
      '了解しました。進捗ログを確認し、タスク優先度に沿って次のアクションプランをまとめます。';

    const assistantMessage: ChatMessage = {
      id: `assistant-${Date.now()}`,
      role: 'assistant',
      content: mockResponse,
      animateKey: `${Date.now()}`
    };

    // Simulate network latency
    await new Promise((resolve) => setTimeout(resolve, 300));
    setMessages((prev) => [...prev, assistantMessage]);
    setPending(false);
  };

  return (
    <main>
      <h1>チャット</h1>
      <p className="description">
        回答が一文字ずつ打ち込まれるアニメーションで表示されます。メッセージを送信すると、アシスタントの返答がタイプライター風に再生されます。
      </p>

      <div className="chat-panel">
        <div className="message-list" ref={listRef}>
          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}
        </div>

        <div className="input-row">
          <textarea
            placeholder="聞きたいことを入力..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
              }
            }}
          />
          <button className="button" onClick={sendMessage} disabled={pending}>
            {pending ? '送信中…' : '送信'}
          </button>
        </div>
        <div className="system-note">※バックエンド接続が必要な場合は sendMessage 内に API 呼び出しを追加してください。</div>
      </div>
      <div className="helper-text">
        返答はタイプライター風に描画され、進捗バーと点滅カーソルで「打ち込み中」であることを視覚的に示します。
      </div>
    </main>
  );
}
