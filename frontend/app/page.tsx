import Link from 'next/link';

export default function Home() {
  return (
    <main>
      <h1>SSP フロントエンド</h1>
      <p className="description">チャット体験のプレビューへ移動します。</p>
      <Link className="button" href="/chat">
        チャット画面を開く
      </Link>
    </main>
  );
}
