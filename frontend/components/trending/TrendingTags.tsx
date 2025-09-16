import React from 'react';

async function fetchTrending(): Promise<string[]> {
  try {
    const res = await fetch('/api/tags/trending', { cache: 'no-store' });
    const data = await res.json();
    return data.tags || [];
  } catch {
    return [];
  }
}

export async function TrendingTags() {
  const tags = await fetchTrending();
  return (
    <div className="bg-white/70 backdrop-blur-sm border rounded-xl p-4 shadow-sm flex flex-col gap-3">
      <h3 className="text-sm font-medium text-neutral-700">トレンド</h3>
      <ul className="flex flex-col gap-2">
        {tags.length === 0 && <li className="text-xs text-neutral-400">トレンドなし</li>}
        {tags.map(t => (
          <li key={t} className="text-xs text-neutral-700 hover:text-indigo-600 cursor-pointer transition-colors">#{t}</li>
        ))}
      </ul>
    </div>
  );
}
