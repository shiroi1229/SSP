import './globals.css';
import type { ReactNode } from 'react';

export const metadata = {
  title: 'SSP Chat',
  description: 'Chat interface with typewriter responses'
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="ja">
      <body>{children}</body>
    </html>
  );
}
