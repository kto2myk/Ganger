import React from 'react';
import { PostList } from '../../components/post/PostList';
import { SearchBox } from '../../components/search/SearchBox';
import { TrendingTags } from '../../components/trending/TrendingTags';
import { FloatingPostButton } from '../../components/post/FloatingPostButton';

export const dynamic = 'force-dynamic';

export default async function HomePage() {
  // Fetch initial posts (server component)
  const res = await fetch(`${process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000'}/api/posts`, { cache: 'no-store' });
  const data = await res.json().catch(() => ({ posts: [], nextCursor: null }));
  const posts = Array.isArray(data.posts) ? data.posts : [];
  const nextCursor = data.nextCursor ?? null;

  return (
    <div className="flex w-full gap-6">
      <div className="flex-1 max-w-2xl">
  <PostList initialPosts={posts} initialNextCursor={nextCursor} />
      </div>
      <aside className="hidden lg:flex flex-col w-80 shrink-0 gap-6">
        <SearchBox />
        <TrendingTags />
      </aside>
      <FloatingPostButton />
    </div>
  );
}
