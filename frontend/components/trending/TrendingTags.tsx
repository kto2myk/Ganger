'use client';

import React, { useState, useEffect } from 'react';

export function TrendingTags() {
  const [tags, setTags] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchTrending = async () => {
      try {
        const res = await fetch('/api/tags/trending', { cache: 'no-store' });
        const data = await res.json();
        setTags(data.tags || []);
      } catch (error) {
        console.error('トレンドタグの取得に失敗しました:', error);
        setTags([]);
      } finally {
        setLoading(false);
      }
    };

    fetchTrending();
  }, []);

  return (
    <div className="bg-white/70 backdrop-blur-sm border rounded-xl p-4 shadow-sm flex flex-col gap-3">
      <h3 className="text-sm font-medium text-neutral-700">トレンド</h3>
      <ul className="flex flex-col gap-2">
        {loading && <li className="text-xs text-neutral-400">読み込み中...</li>}
        {!loading && tags.length === 0 && <li className="text-xs text-neutral-400">トレンドなし</li>}
        {tags.map(t => (
          <li key={t} className="text-xs text-neutral-700 hover:text-indigo-600 cursor-pointer transition-colors">#{t}</li>
        ))}
      </ul>
    </div>
  );
}
