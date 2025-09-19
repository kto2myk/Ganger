'use client';
import React, { useState, useCallback } from 'react';
import { PostCard } from './PostCard';
import { useInfiniteScroll } from '../../lib/useInfiniteScroll';

interface PostListProps { 
  initialPosts: any[]; 
  initialNextCursor?: string | null;
  onPostAdded?: (post: any) => void;
}

export function PostList({ initialPosts, initialNextCursor, onPostAdded }: PostListProps) {
  const [posts, setPosts] = useState(initialPosts);
  const [nextCursor, setNextCursor] = useState<string | null | undefined>(initialNextCursor);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 新しい投稿を先頭に追加する関数
  const addNewPost = (newPost: any) => {
    setPosts(prevPosts => [newPost, ...prevPosts]);
  };

  // onPostAddedが変更された時に関数を更新
  React.useEffect(() => {
    if (onPostAdded) {
      onPostAdded(addNewPost);
    }
  }, [onPostAdded]);

  const loadMore = useCallback(async () => {
    if (loadingMore || !nextCursor) return;
    
    setLoadingMore(true);
    setError(null);
    
    try {
      const res = await fetch(`/api/posts?cursor=${nextCursor}`);
      
      if (!res.ok) {
        throw new Error(`読み込みエラー: ${res.status}`);
      }
      
      const data = await res.json();
      
      if (Array.isArray(data.posts)) {
        setPosts(prevPosts => [...prevPosts, ...data.posts]);
        setNextCursor(data.nextCursor);
      }
    } catch (err) {
      console.error('投稿読み込みエラー:', err);
      setError(err instanceof Error ? err.message : '投稿の読み込みに失敗しました');
    } finally {
      setLoadingMore(false);
    }
  }, [loadingMore, nextCursor]);

  // 無限スクロールのトリガー要素の参照
  const triggerRef = useInfiniteScroll(
    loadMore,
    loadingMore,
    !!nextCursor,
    { 
      threshold: 0.5, // 要素の50%が見えたら読み込み開始
      rootMargin: '200px' // 200px前から読み込み準備
    }
  );

  if (posts.length === 0) {
    return <div className="text-sm text-neutral-500">投稿はまだありません。</div>;
  }

  return (
    <div className="flex flex-col gap-4">
      {posts.map(p => <PostCard key={p.id} post={p} />)}
      
      {/* 無限スクロールのトリガー要素 */}
      {nextCursor && (
        <div ref={triggerRef} className="flex justify-center py-4">
          {loadingMore ? (
            <div className="flex items-center gap-2 text-sm text-neutral-500">
              <div className="w-4 h-4 border-2 border-blue-200 border-t-blue-600 rounded-full animate-spin"></div>
              読み込み中...
            </div>
          ) : error ? (
            <div className="text-sm text-red-500 bg-red-50 px-3 py-2 rounded-md">
              {error}
              <button 
                onClick={loadMore}
                className="ml-2 text-blue-600 hover:text-blue-700 underline"
              >
                再試行
              </button>
            </div>
          ) : (
            <div className="text-xs text-neutral-400">
              スクロールして続きを読み込み
            </div>
          )}
        </div>
      )}
      
      {!nextCursor && posts.length > 0 && (
        <div className="text-center py-4 text-sm text-neutral-400">
          すべての投稿を表示しました
        </div>
      )}
    </div>
  );
}
