import './globals.css';
import type { Metadata } from 'next';
import React from 'react';
import { SessionProvider } from 'next-auth/react';
import { Sidebar } from '../components/layout/Sidebar';

export const metadata: Metadata = {
  title: 'Ganger',
  description: 'Ganger frontend (Next.js skeleton)'
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ja">
      <body>
        <SessionProvider>
          <div className="flex min-h-screen">
            <Sidebar />
            <div className="flex-1 flex flex-col">
              <header className="h-14 border-b flex items-center px-4 bg-white/60 backdrop-blur-sm sticky top-0 z-10"> 
                <strong className="text-neutral-700">Ganger</strong>
              </header>
              <main className="flex-1 p-4">{children}</main>
            </div>
          </div>
        </SessionProvider>
        <footer style={{ padding: '1rem', borderTop: '1px solid #eee', fontSize: 12 }}>
          Skeleton – replace with real layout.
        </footer>
      </body>
    </html>
  );
}
