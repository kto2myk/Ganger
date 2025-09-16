'use client';
import Link from 'next/link';
import { Plus } from 'lucide-react';
export function FloatingPostButton() {
  return (
    <Link href="/post/create" className="fixed bottom-16 right-8 md:right-16">
      <span className="h-14 w-14 md:h-16 md:w-16 rounded-full bg-gradient-to-br from-indigo-500 to-indigo-600 shadow-lg flex items-center justify-center text-white hover:from-indigo-600 hover:to-indigo-700 transition-colors">
        <Plus size={28} />
      </span>
    </Link>
  );
}
