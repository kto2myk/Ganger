import React from 'react';
import { headers } from 'next/headers';
import HomePage from './HomePage';

export const dynamic = 'force-dynamic';

export default async function HomePageWrapper() {
  // Fetch initial posts (server component) with fallback strategy
  let data: any = { posts: [], nextCursor: null };
  try {
    const h = headers();
    const proto = h.get('x-forwarded-proto') || 'http';
    const host = h.get('x-forwarded-host') || h.get('host') || 'localhost:3000';
    const base = process.env.NEXT_PUBLIC_APP_URL || `${proto}://${host}`;
    const res = await fetch(`${base}/api/posts`, { cache: 'no-store' });
    if (res.ok) {
      data = await res.json().catch(() => data);
    } else {
      console.warn('posts fetch non-ok status', res.status);
    }
  } catch (e) {
    console.error('Home fetch error', e);
  }
  let posts = Array.isArray(data.posts) ? data.posts : [];
  if (posts.length === 0) {
    // 仮表示用ダミーポスト
    const now = Date.now();
    posts = [
      {
        id: 'demo1',
        content: 'ようこそ Ganger (Next.js 移行版) へ！これはダミー投稿です。\n本番データがまだ無い場合に一時的に表示されます。',
        createdAt: now - 1000 * 60 * 5,
        author: { id: 'u_demo', username: 'demo_user' },
        images: [],
        tags: [],
        likes: []
      },
      {
        id: 'demo2',
        content: '2件目の仮投稿。APIやDB接続 (Prisma + SQLite) が整ったらこのプレースホルダは消えます。',
        createdAt: now - 1000 * 60 * 10,
        author: { id: 'u_system', username: 'system' },
        images: [
          { id: 'img1', url: 'https://picsum.photos/seed/ganger-demo/600/400' }
        ],
        tags: [{ id: 'ptag1', tag: 'demo' }],
        likes: [{ id: 'like1' }]
      }
    ];
  }
  const nextCursor = data.nextCursor ?? null;

  return <HomePage initialPosts={posts} initialNextCursor={nextCursor} />;
}
