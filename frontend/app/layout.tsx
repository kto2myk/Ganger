import './globals.css';
import type { Metadata } from 'next';
import React from 'react';
import { SessionProvider } from 'next-auth/react';
import { Sidebar } from '../components/layout/Sidebar';
import { MobileMenu } from '../components/layout/MobileMenu';
import { SessionWatchdog } from '../components/auth/SessionWatchdog';

export const metadata: Metadata = {
  title: 'Ganger',
  description: 'Ganger frontend (Next.js skeleton)'
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ja">
      <body>
        <SessionProvider 
          refetchInterval={0} // 自動更新を無効化
          refetchOnWindowFocus={true} // ウィンドウフォーカス時のみ更新
        >
          <SessionWatchdog />
          <div className="flex min-h-screen">
            <Sidebar />
            <div className="flex-1 flex flex-col md:ml-56">
              <header className="h-16 border-b border-gray-200/60 flex items-center justify-between px-6 bg-white/80 backdrop-blur-md sticky top-0 z-20 shadow-sm"> 
                <div className="flex items-center gap-4">
                  {/* モバイル用ハンバーガーメニュー */}
                  <MobileMenu />
                  {/* ロゴ・ブランド */}
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center">
                      <span className="text-white font-bold text-sm">G</span>
                    </div>
                    <h1 className="text-xl font-bold text-gray-800 hidden sm:block">Ganger</h1>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  {/* 将来の検索、通知アイコンなど */}
                  <div className="hidden sm:flex items-center gap-2 text-sm text-gray-500">
                    Social Network
                  </div>
                </div>
              </header>
              <main className="flex-1 p-4">{children}</main>
            </div>
          </div>
        </SessionProvider>
        <footer className="bg-gray-50 border-t border-gray-200 px-6 py-4 text-center">
          <div className="max-w-4xl mx-auto">
            <p className="text-sm text-gray-500">
              © 2024 Ganger - ソーシャルネットワークプラットフォーム
            </p>
          </div>
        </footer>
      </body>
    </html>
  );
}
