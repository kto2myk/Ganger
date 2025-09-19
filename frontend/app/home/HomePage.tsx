'use client';

import React, { useState, useCallback } from 'react';
import { PostList } from '@/components/post/PostList';
import { SearchBox } from '@/components/search/SearchBox';
import { TrendingTags } from '@/components/trending/TrendingTags';
import { InlinePostCreator } from '@/components/post/InlinePostCreator';
import { useRequireAuth } from '@/lib/useAuthRedirect';

interface HomePageProps {
  initialPosts: any[];
  initialNextCursor: string | null;
}

export default function HomePage({ initialPosts, initialNextCursor }: HomePageProps) {
  // 認証が必要なページなので、未認証の場合はログインページにリダイレクト
  const { session, isLoading } = useRequireAuth();

  const handlePostCreated = useCallback(() => {
    // 投稿作成後にページを更新
    window.location.reload();
  }, []);

  // 認証チェック中はローディング表示
  if (isLoading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="text-gray-500">読み込み中...</div>
      </div>
    );
  }

  return (
    <div className="flex w-full gap-6">
      <div className="flex-1 max-w-2xl">
        <InlinePostCreator onPostCreated={handlePostCreated} />
        <PostList initialPosts={initialPosts} initialNextCursor={initialNextCursor} />
      </div>
      <aside className="hidden lg:flex flex-col w-80 shrink-0 gap-6">
        <SearchBox />
        <TrendingTags />
      </aside>
    </div>
  );
}