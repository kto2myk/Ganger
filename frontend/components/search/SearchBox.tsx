import React from 'react';
import { Search } from 'lucide-react';
export function SearchBox() {
  return (
    <div className="bg-white/70 backdrop-blur-sm border rounded-xl p-4 flex items-center gap-2 shadow-sm">
      <Search size={18} className="text-neutral-500" />
      <input
        type="text"
        placeholder="検索..."
        className="flex-1 bg-transparent outline-none text-sm placeholder:text-neutral-400"
      />
    </div>
  );
}
