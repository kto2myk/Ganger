import Link from 'next/link';
import { Home, Search, Bell, MessageSquare, ShoppingCart, User, Shield, LogOut, PenTool } from 'lucide-react';

const nav = [
  { href: '/home', label: 'HOME', icon: Home },
  { href: '/search', label: '検索', icon: Search },
  { href: '/notifications', label: 'お知らせ', icon: Bell },
  { href: '/messages', label: 'メッセージ', icon: MessageSquare },
  { href: '/cart', label: 'カート', icon: ShoppingCart },
  { href: '/me', label: 'プロフィール', icon: User },
  { href: '/design/create', label: 'Design', icon: PenTool },
];

export function Sidebar() {
  return (
    <aside className="hidden md:flex flex-col w-56 shrink-0 border-r bg-white/70 backdrop-blur-sm min-h-screen py-6 px-4 gap-4">
      <Link href="/" className="flex items-center gap-2 mb-4 font-semibold text-lg">
        <span className="text-indigo-600">Ganger</span>
      </Link>
      <nav className="flex flex-col gap-1">
        {nav.map(item => {
          const Icon = item.icon;
          return (
            <Link key={item.href} href={item.href} className="flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium hover:bg-indigo-50 text-neutral-700 hover:text-indigo-700 transition-colors">
              <Icon size={18} /> {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="mt-auto pt-4 border-t">
        <form action="/api/auth/signout" method="post">
          <button className="w-full text-left flex items-center gap-3 px-3 py-2 rounded-md text-sm text-neutral-600 hover:bg-rose-50 hover:text-rose-600 transition-colors">
            <LogOut size={18} /> ログアウト
          </button>
        </form>
      </div>
    </aside>
  );
}
