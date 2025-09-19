'use client';

import React, { useState } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { Heart, MessageCircle, Share, ChevronLeft, ChevronRight, User } from 'lucide-react';
import { CommentSection } from './CommentSection';

// プロフィール画像のパスを処理するヘルパー関数
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

interface PostDetailModalProps {
  post: {
    id: string;
    content: string;
    createdAt: Date;
    author: {
      id: string;
      username: string;
      email: string;
      image?: string | null;
      profileImage?: string | null;
      bio?: string | null;
      createdAt: Date;
    };
    images: Array<{
      id: string;
      url: string;
      order: number;
    }>;
    tags: Array<{
      id: string;
      tag: string;
    }>;
    likes: Array<{
      id: string;
      user: {
        id: string;
        username: string;
      };
    }>;
    comments: Array<{
      id: string;
      content: string;
      createdAt: Date;
      author: {
        id: string;
        username: string;
        image?: string | null;
        profileImage?: string | null;
      };
    }>;
    reposts: Array<{
      id: string;
      user: {
        id: string;
        username: string;
      };
    }>;
    _count: {
      likes: number;
      comments: number;
      reposts: number;
    };
  };
}

export function PostDetailModal({ post }: PostDetailModalProps) {
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [isLiked, setIsLiked] = useState(false); // TODO: 実際のいいね状態を取得
  const [likeCount, setLikeCount] = useState(post?._count?.likes || 0);

  // データの有効性チェック
  if (!post || !post.id) {
    return (
      <div className="flex items-center justify-center p-8">
        <span className="text-gray-500">投稿データを読み込めませんでした</span>
      </div>
    );
  }

  // 安全な値の設定
  const safePost = {
    ...post,
    images: post.images || [],
    author: post.author || { username: 'Unknown', id: '', email: '', createdAt: new Date() },
    tags: post.tags || [],
    comments: post.comments || [],
    _count: post._count || { likes: 0, comments: 0, reposts: 0 }
  };

  const handleLike = async () => {
    // TODO: いいねAPIを呼び出す
    setIsLiked(!isLiked);
    setLikeCount(prev => isLiked ? prev - 1 : prev + 1);
  };

  const nextImage = () => {
    setCurrentImageIndex((prev) => 
      prev === safePost.images.length - 1 ? 0 : prev + 1
    );
  };

  const prevImage = () => {
    setCurrentImageIndex((prev) => 
      prev === 0 ? safePost.images.length - 1 : prev - 1
    );
  };

  const formatDate = (date: Date) => {
    return new Date(date).toLocaleString('ja-JP', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="flex flex-col md:flex-row max-h-[90vh]">
      {/* 左側: 画像表示 (モバイルでは上部) */}
      {safePost.images && safePost.images.length > 0 && (
        <div className="md:flex-1 md:max-w-2xl">
          <div className="relative aspect-square bg-black overflow-hidden">
            {safePost.images[currentImageIndex] && safePost.images[currentImageIndex].url ? (
              <Image
                src={safePost.images[currentImageIndex].url}
                alt={`投稿画像 ${currentImageIndex + 1}`}
                fill
                className="object-contain"
                priority
                onError={(e) => {
                  console.error('画像読み込みエラー:', safePost.images[currentImageIndex].url);
                  e.currentTarget.style.display = 'none';
                }}
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-white">
                画像を読み込めませんでした
              </div>
            )}
            
            {safePost.images.length > 1 && (
              <>
                <button
                  onClick={prevImage}
                  className="absolute left-4 top-1/2 transform -translate-y-1/2 bg-black/50 hover:bg-black/70 text-white p-2 rounded-full transition-all"
                >
                  <ChevronLeft className="w-5 h-5" />
                </button>
                <button
                  onClick={nextImage}
                  className="absolute right-4 top-1/2 transform -translate-y-1/2 bg-black/50 hover:bg-black/70 text-white p-2 rounded-full transition-all"
                >
                  <ChevronRight className="w-5 h-5" />
                </button>
                
                {/* 画像インジケーター */}
                <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 flex space-x-2">
                  {safePost.images.map((_, index) => (
                    <button
                      key={index}
                      onClick={() => setCurrentImageIndex(index)}
                      className={`w-2 h-2 rounded-full transition-all ${
                        index === currentImageIndex 
                          ? 'bg-white' 
                          : 'bg-white bg-opacity-50'
                      }`}
                    />
                  ))}
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {/* 右側: 投稿情報とコメント (モバイルでは下部) */}
      <div className="md:w-96 flex flex-col">
        {/* 投稿者情報 */}
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center">
            <div className="w-10 h-10 bg-gray-300 rounded-full overflow-hidden mr-3">
              {(() => {
                const profileImageSrc = getProfileImageSrc(safePost.author?.image, safePost.author?.profileImage);
                return profileImageSrc ? (
                  <Image
                    src={profileImageSrc}
                    alt={`${safePost.author?.username || 'ユーザー'}のプロフィール`}
                    width={40}
                    height={40}
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      console.error('プロフィール画像読み込みエラー:', profileImageSrc);
                      e.currentTarget.style.display = 'none';
                    }}
                  />
                ) : (
                  <div className="w-full h-full bg-gray-400 flex items-center justify-center text-white font-bold">
                    <User className="w-5 h-5" />
                  </div>
                );
              })()}
            </div>
            <div className="flex-1">
              <Link 
                href={`/profile/${safePost.author.username}`}
                className="font-semibold text-gray-900 hover:text-blue-600 transition-colors text-sm no-underline hover:no-underline"
              >
                {safePost.author.username}
              </Link>
              <p className="text-xs text-gray-500">
                {formatDate(safePost.createdAt)}
              </p>
            </div>
          </div>
        </div>

        {/* 投稿内容 */}
        <div className="flex-1 overflow-y-auto">
          <div className="p-4">
            <p className="text-sm text-gray-900 leading-relaxed whitespace-pre-wrap mb-3">
              {safePost.content}
            </p>
            
            {/* タグ */}
            {safePost.tags.length > 0 && (
              <div className="flex flex-wrap gap-1 mb-3">
                {safePost.tags.map((tag) => (
                  <Link
                    key={tag.id}
                    href={`/search?tag=${encodeURIComponent(tag.tag)}`}
                    className="text-blue-600 hover:text-blue-700 text-xs bg-blue-50 px-2 py-1 rounded-full transition-colors"
                  >
                    #{tag.tag}
                  </Link>
                ))}
              </div>
            )}

            {/* アクションボタン */}
            <div className="flex items-center space-x-4 py-2 border-y border-gray-100">
              <button
                onClick={handleLike}
                className={`flex items-center space-x-1 transition-colors ${
                  isLiked ? 'text-red-500' : 'text-gray-600 hover:text-red-500'
                }`}
              >
                <Heart className={`w-5 h-5 ${isLiked ? 'fill-current' : ''}`} />
                <span className="text-sm">{likeCount}</span>
              </button>
              
              <div className="flex items-center space-x-1 text-gray-600">
                <MessageCircle className="w-5 h-5" />
                <span className="text-sm">{safePost._count.comments}</span>
              </div>
              
              <div className="flex items-center space-x-1 text-gray-600">
                <Share className="w-5 h-5" />
                <span className="text-sm">{safePost._count.reposts}</span>
              </div>
            </div>
          </div>

          {/* コメントセクション */}
          <div className="border-t border-gray-100">
            <CommentSection 
              postId={safePost.id} 
              comments={safePost.comments}
              commentCount={safePost._count.comments}
              compact={true}
            />
          </div>
        </div>
      </div>
    </div>
  );
}