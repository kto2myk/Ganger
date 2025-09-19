'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useSession } from 'next-auth/react';
import { Menu, X, Home, Search, Bell, MessageSquare, ShoppingCart, User, LogOut, PenTool } from 'lucide-react';

const nav = [
  { href: '/home', label: 'HOME', icon: Home },
  { href: '/search', label: '検索', icon: Search },
  { href: '/notifications', label: 'お知らせ', icon: Bell },
  { href: '/messages', label: 'メッセージ', icon: MessageSquare },
  { href: '/cart', label: 'カート', icon: ShoppingCart },
  { href: '/design/create', label: 'Design', icon: PenTool },
];

export function MobileMenu() {
  const [isOpen, setIsOpen] = useState(false);
  const { data: session } = useSession();

  // メニューが開いている時はスクロールを無効化
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }

    // クリーンアップ
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  // ESCキーでメニューを閉じる
  useEffect(() => {
    const handleEsc = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsOpen(false);
      }
    };
    
    if (isOpen) {
      document.addEventListener('keydown', handleEsc);
    }
    
    return () => {
      document.removeEventListener('keydown', handleEsc);
    };
  }, [isOpen]);

  const handleLinkClick = () => {
    setIsOpen(false);
  };

  return (
    <>
      {/* ハンバーガーメニューボタン - モバイルのみ表示 */}
      <button
        onClick={() => setIsOpen(true)}
        className="md:hidden p-2 rounded-lg hover:bg-gray-100 transition-colors relative"
        aria-label="メニューを開く"
      >
        <Menu size={24} className="text-gray-700" />
        {/* 視覚的なハイライト */}
        <div className="absolute inset-0 rounded-lg border-2 border-transparent hover:border-indigo-200 transition-colors" />
      </button>

      {/* オーバーレイ */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 md:hidden"
          onClick={() => setIsOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* サイドメニュー */}
      <aside
        className={`
          fixed top-0 left-0 z-50 w-80 h-full bg-gradient-to-br from-white to-gray-50 shadow-2xl transform transition-transform duration-300 ease-in-out md:hidden border-r border-gray-200
          ${isOpen ? 'translate-x-0' : '-translate-x-full'}
        `}
      >
        {/* ヘッダー */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 bg-white/80 backdrop-blur-sm">
          <Link 
            href="/" 
            className="flex items-center gap-2 font-bold text-xl text-indigo-600 no-underline hover:no-underline"
            onClick={handleLinkClick}
          >
            <div className="w-8 h-8 bg-gradient-to-br from-indigo-500 to-indigo-700 rounded-lg flex items-center justify-center text-white text-sm font-bold">
              G
            </div>
            Ganger
          </Link>
          <button
            onClick={() => setIsOpen(false)}
            className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
            aria-label="メニューを閉じる"
          >
            <X size={20} className="text-gray-500" />
          </button>
        </div>

        {/* ナビゲーション */}
        <nav className="flex flex-col p-6 space-y-2 flex-1">
          {nav.map((item) => {
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={handleLinkClick}
                className="flex items-center gap-4 rounded-xl px-4 py-4 text-base font-medium hover:bg-indigo-50 text-neutral-700 hover:text-indigo-700 transition-all duration-200 hover:translate-x-1 hover:shadow-sm no-underline hover:no-underline"
              >
                <div className="flex items-center justify-center w-10 h-10 bg-gray-100 rounded-lg">
                  <Icon size={20} className="text-neutral-600" />
                </div>
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* 下部のボタン群 */}
        <div className="p-6 border-t border-gray-200 space-y-3 bg-white/80 backdrop-blur-sm">
          {/* プロフィールボタン */}
          {session?.user && (
            <Link
              href="/profile/testuser"
              onClick={handleLinkClick}
              className="flex items-center gap-4 px-4 py-4 rounded-xl text-base font-medium hover:bg-indigo-50 text-neutral-700 hover:text-indigo-700 transition-all duration-200 hover:translate-x-1 hover:shadow-sm no-underline hover:no-underline"
            >
              <div className="flex items-center justify-center w-10 h-10 bg-indigo-100 rounded-lg">
                <User size={20} className="text-indigo-600" />
              </div>
              <span>プロフィール</span>
            </Link>
          )}

          {/* ログアウトボタン */}
          <form action="/api/auth/signout" method="post">
            <button
              type="submit"
              className="w-full flex items-center gap-4 px-4 py-4 rounded-xl text-base font-medium text-neutral-600 hover:bg-red-50 hover:text-red-600 transition-all duration-200 hover:translate-x-1 hover:shadow-sm"
              onClick={() => setIsOpen(false)}
            >
              <div className="flex items-center justify-center w-10 h-10 bg-red-100 rounded-lg">
                <LogOut size={20} className="text-red-500" />
              </div>
              <span>ログアウト</span>
            </button>
          </form>
        </div>
      </aside>
    </>
  );
}