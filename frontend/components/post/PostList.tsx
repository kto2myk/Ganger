'use client';
import React, { useState } from 'react';
import { PostCard } from './PostCard';

interface PostListProps { initialPosts: any[]; initialNextCursor?: string | null }

export function PostList({ initialPosts, initialNextCursor }: PostListProps) {
  const [posts, setPosts] = useState(initialPosts);
  const [nextCursor, setNextCursor] = useState<string | null | undefined>(initialNextCursor);
  const [loadingMore, setLoadingMore] = useState(false);

  async function loadMore() {
    setLoadingMore(true);
    try {
      if (!nextCursor) return;
      const res = await fetch(`/api/posts?cursor=${nextCursor}`);
      const data = await res.json();
      if (Array.isArray(data.posts)) setPosts(p => [...p, ...data.posts]);
      setNextCursor(data.nextCursor);
    } finally {
      setLoadingMore(false);
    }
  }

  if (posts.length === 0) {
    return <div className="text-sm text-neutral-500">投稿はまだありません。</div>;
  }

  return (
    <div className="flex flex-col gap-4">
      {posts.map(p => <PostCard key={p.id} post={p} />)}
      {nextCursor && (
        <div className="flex justify-center">
          <button disabled={loadingMore} onClick={loadMore} className="px-4 py-2 text-sm rounded-md border bg-white hover:bg-neutral-50 disabled:opacity-50">
            {loadingMore ? '読み込み中...' : 'さらに読み込む'}
          </button>
        </div>
      )}
    </div>
  );
}
