import './globals.css';
import type { Metadata } from 'next';
import React from 'react';

export const metadata: Metadata = {
  title: 'Ganger',
  description: 'Ganger frontend (Next.js skeleton)'
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ja">
      <body>
        <header style={{ padding: '0.75rem 1rem', borderBottom: '1px solid #eee' }}>
          <strong>Ganger</strong>
        </header>
        <main style={{ padding: '1rem', minHeight: '80vh' }}>{children}</main>
        <footer style={{ padding: '1rem', borderTop: '1px solid #eee', fontSize: 12 }}>
          Skeleton – replace with real layout.
        </footer>
      </body>
    </html>
  );
}
