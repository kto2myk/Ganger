'use client';

import Link from 'next/link';
import { useSession } from 'next-auth/react';
import { Home, Search, Bell, MessageSquare, ShoppingCart, User, Shield, LogOut, PenTool } from 'lucide-react';

const nav = [
  { href: '/home', label: 'HOME', icon: Home },
  { href: '/search', label: '検索', icon: Search },
  { href: '/notifications', label: 'お知らせ', icon: Bell },
  { href: '/messages', label: 'メッセージ', icon: MessageSquare },
  { href: '/cart', label: 'カート', icon: ShoppingCart },
  { href: '/design/create', label: 'Design', icon: PenTool },
];

export function Sidebar() {
  const { data: session } = useSession();
  
  return (
    <aside className="hidden md:flex fixed left-0 top-0 z-30 flex-col w-56 bg-white/90 backdrop-blur-md h-screen py-6 px-4 gap-4 border-r border-gray-200 shadow-sm overflow-y-auto">
      <Link href="/" className="flex items-center gap-2 mb-4 font-semibold text-lg no-underline hover:no-underline">
        <span className="text-indigo-600">Ganger</span>
      </Link>
      <nav className="flex flex-col gap-1">
        {nav.map(item => {
          const Icon = item.icon;
          return (
            <Link key={item.href} href={item.href} className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium hover:bg-indigo-50 text-neutral-700 hover:text-indigo-700 transition-all duration-200 hover:translate-x-1 no-underline hover:no-underline">
              <Icon size={18} className="text-neutral-500" /> 
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>
      <div className="mt-auto pt-4 border-t border-gray-200 space-y-2">
        {/* プロフィールボタン - ログアウトの上に配置 */}
        {session?.user && (
          <Link 
            href={`/profile/testuser`} 
            className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium hover:bg-indigo-50 text-neutral-700 hover:text-indigo-700 transition-all duration-200 hover:translate-x-1 no-underline hover:no-underline"
          >
            <User size={18} className="text-neutral-500" />
            <span>プロフィール</span>
          </Link>
        )}
        
        {/* ログアウトボタン */}
        <form action="/api/auth/signout" method="post">
          <button className="w-full text-left flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-neutral-600 hover:bg-red-50 hover:text-red-600 transition-all duration-200">
            <LogOut size={18} className="text-neutral-500" /> 
            <span>ログアウト</span>
          </button>
        </form>
      </div>
    </aside>
  );
}
