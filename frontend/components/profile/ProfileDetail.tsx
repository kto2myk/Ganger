'use client';

import React, { useState, useCallback } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { useSession } from 'next-auth/react';
import { Calendar, MapPin, MessageCircle, UserPlus, Settings, Edit, User } from 'lucide-react';
import { PostCard } from '@/components/post/PostCard';

/**
 * プロフィール画像のパスを適切な形式に変換するヘルパー関数
 * 相対パス、絶対パス、URLを統一的に処理し、デフォルト画像のフォールバックを提供
 * @param image - ユーザーのimageフィールド
 * @param profileImage - ユーザーのprofileImageフィールド  
 * @returns 処理済みの画像パスまたはnull
 */
function getProfileImageSrc(image: string | null | undefined, profileImage: string | null | undefined): string | null {
  const imageSrc = image || profileImage;
  if (!imageSrc) return null;
  
  // 既に絶対パスまたはURLの場合はそのまま返す
  if (imageSrc.startsWith('/') || imageSrc.startsWith('http')) {
    return imageSrc;
  }
  
  // 相対パスの場合は絶対パスに変換
  if (imageSrc === 'default-profile.png') {
    return '/default-profile.svg';
  }
  
  // その他の相対パスは/uploadsに配置されていると仮定
  return `/uploads/${imageSrc}`;
}

interface ProfileDetailProps {
  user: {
    id: string;
    username: string;
    email: string;
    realName?: string | null;
    bio?: string | null;
    address?: string | null;
    image?: string | null;
    profileImage?: string | null;
    createdAt: Date;
    _count: {
      posts: number;
      followers: number;
      following: number;
    };
  };
  initialPosts: any[];
  initialNextCursor: string | null;
}

export function ProfileDetail({ user, initialPosts, initialNextCursor }: ProfileDetailProps) {
  const { data: session } = useSession();
  const [posts, setPosts] = useState(initialPosts);
  const [nextCursor, setNextCursor] = useState(initialNextCursor);
  const [loading, setLoading] = useState(false);
  const [hasNextPage, setHasNextPage] = useState(Boolean(initialNextCursor));

  const isOwnProfile = session?.user?.email === user.email;
  const profileImageSrc = getProfileImageSrc(user.image, user.profileImage);

  // 投稿の無限スクロール読み込み
  const loadMorePosts = useCallback(async () => {
    if (loading || !hasNextPage) return;

    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (nextCursor) params.set('cursor', nextCursor);
      params.set('limit', '10');

      const response = await fetch(`/api/users/${user.username}/posts?${params}`);
      if (response.ok) {
        const data = await response.json();
        setPosts(prev => [...prev, ...data.posts]);
        setNextCursor(data.nextCursor);
        setHasNextPage(data.hasNextPage);
      }
    } catch (error) {
      console.error('投稿の読み込みに失敗しました:', error);
    } finally {
      setLoading(false);
    }
  }, [loading, hasNextPage, nextCursor, user.username]);

  // 新しい投稿が作成された時の処理
  const handleNewPost = useCallback((newPost: any) => {
    setPosts(prev => [newPost, ...prev]);
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50">
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* プロフィールヘッダー */}
        <div className="bg-white rounded-xl shadow-sm border p-6 mb-6">
          <div className="flex flex-col md:flex-row gap-6">
            {/* プロフィール画像 */}
            <div className="flex-shrink-0">
              <div className="w-32 h-32 bg-gray-300 rounded-full overflow-hidden">
                {profileImageSrc ? (
                  <Image
                    src={profileImageSrc}
                    alt={`${user.username}のプロフィール`}
                    width={128}
                    height={128}
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      console.error('プロフィール画像読み込みエラー:', profileImageSrc);
                      e.currentTarget.style.display = 'none';
                    }}
                  />
                ) : (
                  <div className="w-full h-full bg-gray-400 flex items-center justify-center text-white">
                    <User className="w-12 h-12" />
                  </div>
                )}
              </div>
            </div>

            {/* ユーザー情報 */}
            <div className="flex-1">
              <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 mb-4">
                <div>
                  <h1 className="text-2xl font-bold text-gray-900">
                    {user.realName || user.username}
                  </h1>
                  <p className="text-gray-600">@{user.username}</p>
                </div>

                {/* アクションボタン */}
                <div className="flex gap-2">
                  {isOwnProfile ? (
                    <>
                      <Link
                        href="/me/edit"
                        className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors no-underline hover:no-underline"
                      >
                        <Edit className="w-4 h-4" />
                        プロフィール編集
                      </Link>
                      <Link
                        href="/me/settings"
                        className="flex items-center gap-2 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors no-underline hover:no-underline"
                      >
                        <Settings className="w-4 h-4" />
                        設定
                      </Link>
                    </>
                  ) : (
                    <>
                      <button className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors">
                        <UserPlus className="w-4 h-4" />
                        フォロー
                      </button>
                      <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                        <MessageCircle className="w-4 h-4" />
                        メッセージ
                      </button>
                    </>
                  )}
                </div>
              </div>

              {/* バイオ */}
              {user.bio && (
                <p className="text-gray-700 mb-4">{user.bio}</p>
              )}

              {/* メタ情報 */}
              <div className="flex flex-wrap gap-4 text-sm text-gray-600 mb-4">
                {user.address && (
                  <div className="flex items-center gap-1">
                    <MapPin className="w-4 h-4" />
                    <span>{user.address}</span>
                  </div>
                )}
                <div className="flex items-center gap-1">
                  <Calendar className="w-4 h-4" />
                  <span>{new Date(user.createdAt).toLocaleDateString('ja-JP', {
                    year: 'numeric',
                    month: 'long'
                  })}に登録</span>
                </div>
              </div>

              {/* 統計情報 */}
              <div className="flex gap-6 text-sm">
                <div>
                  <span className="font-bold text-gray-900">{user._count.posts}</span>
                  <span className="text-gray-600 ml-1">投稿</span>
                </div>
                <div>
                  <span className="font-bold text-gray-900">{user._count.following}</span>
                  <span className="text-gray-600 ml-1">フォロー中</span>
                </div>
                <div>
                  <span className="font-bold text-gray-900">{user._count.followers}</span>
                  <span className="text-gray-600 ml-1">フォロワー</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 投稿一覧 */}
        <div className="bg-white rounded-xl shadow-sm border">
          <div className="p-4 border-b border-gray-100">
            <h2 className="text-lg font-semibold text-gray-900">投稿</h2>
          </div>
          
          <div className="divide-y divide-gray-100">
            {posts.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                まだ投稿がありません
              </div>
            ) : (
              posts.map(post => (
                <PostCard key={post.id} post={post} />
              ))
            )}
            
            {/* 読み込みボタン */}
            {hasNextPage && (
              <div className="p-4 text-center">
                <button
                  onClick={loadMorePosts}
                  disabled={loading}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? '読み込み中...' : 'もっと見る'}
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}