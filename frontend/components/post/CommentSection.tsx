'use client';

import React, { useState } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { Send } from 'lucide-react';

/**
 * プロフィール画像のパスを適切な形式に変換するヘルパー関数
 * 相対パス、絶対パス、URLを統一的に処理し、フォールバックとしてデフォルト画像を返す
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

interface Comment {
  id: string;
  content: string;
  createdAt: Date;
  author: {
    id: string;
    username: string;
    image?: string | null;
    profileImage?: string | null;
  };
}

interface CommentSectionProps {
  postId: string;
  comments: Comment[];
  commentCount: number;
  compact?: boolean; // モーダル用のコンパクト表示
}

export function CommentSection({ postId, comments, commentCount, compact = false }: CommentSectionProps) {
  // 新しいコメントのテキスト内容
  const [newComment, setNewComment] = useState('');
  // コメント投稿中のローディング状態
  const [isSubmitting, setIsSubmitting] = useState(false);
  // ローカルのコメント一覧（新規投稿時に即座更新用）
  const [localComments, setLocalComments] = useState(comments);

  const formatDate = (date: Date) => {
    return new Date(date).toLocaleString('ja-JP', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  /**
   * コメント投稿フォームの送信処理
   * APIでコメントを作成し、成功時にローカル状態を更新
   * @param e - フォーム送信イベント
   */
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // 空のコメントや送信中の場合は早期リターン
    if (!newComment.trim() || isSubmitting) return;

    setIsSubmitting(true);
    try {
      // コメント作成APIを呼び出し
      const response = await fetch(`/api/posts/${postId}/comments`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'user-email': 'test@example.com' // テスト用の認証ヘッダー
        },
        body: JSON.stringify({
          content: newComment.trim(),
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setLocalComments([data.comment, ...localComments]);
        setNewComment('');
      } else {
        console.error('コメントの投稿に失敗しました');
      }
    } catch (error) {
      console.error('コメントの投稿中にエラーが発生しました:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className={compact ? "" : "border-t border-gray-100"}>
      {/* コメント投稿フォーム */}
      <div className={compact ? "p-3 bg-gray-50" : "px-6 py-4 bg-gray-50"}>
        <form onSubmit={handleSubmit} className="flex space-x-2">
          <div className="flex-1">
            <textarea
              value={newComment}
              onChange={(e) => setNewComment(e.target.value)}
              placeholder="コメントを追加..."
              className={`w-full px-2 py-1 border border-gray-300 rounded resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm ${
                compact ? 'text-xs' : ''
              }`}
              rows={compact ? 1 : 2}
              maxLength={500}
            />
          </div>
          <button
            type="submit"
            disabled={!newComment.trim() || isSubmitting}
            className={`self-end px-2 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-1 ${
              compact ? 'text-xs px-2 py-1' : 'px-4 py-2'
            }`}
          >
            {isSubmitting ? (
              <div className="w-3 h-3 border border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <Send className={compact ? "w-3 h-3" : "w-4 h-4"} />
            )}
            {!compact && <span>投稿</span>}
          </button>
        </form>
        <div className={`text-gray-500 mt-1 ${compact ? 'text-xs' : 'text-xs'}`}>
          {newComment.length}/500
        </div>
      </div>

      {/* コメント一覧 */}
      <div className={compact ? "p-3" : "px-6 py-4"}>
        <h3 className={`font-semibold text-gray-900 mb-3 ${compact ? 'text-sm' : ''}`}>
          コメント ({localComments.length})
        </h3>
        
        {localComments.length === 0 ? (
          <p className={`text-gray-500 text-center py-4 ${compact ? 'text-xs py-2' : ''}`}>
            まだコメントはありません。
          </p>
        ) : (
          <div className={compact ? "space-y-2" : "space-y-4"}>
            {localComments.map((comment) => (
              <div key={comment.id} className={compact ? "flex space-x-2" : "flex space-x-3"}>
                {/* プロフィール画像 */}
                <div className={`bg-gray-300 rounded-full overflow-hidden flex-shrink-0 ${
                  compact ? 'w-6 h-6' : 'w-8 h-8'
                }`}>
                  {(() => {
                    const profileImageSrc = getProfileImageSrc(comment.author.image, comment.author.profileImage);
                    return profileImageSrc ? (
                      <Image
                        src={profileImageSrc}
                        alt={`${comment.author.username}のプロフィール`}
                        width={compact ? 24 : 32}
                        height={compact ? 24 : 32}
                        className="w-full h-full object-cover"
                        onError={(e) => {
                          console.error('プロフィール画像読み込みエラー:', profileImageSrc);
                          e.currentTarget.style.display = 'none';
                        }}
                      />
                    ) : (
                      <div className={`w-full h-full bg-gray-400 flex items-center justify-center text-white font-bold ${
                        compact ? 'text-xs' : 'text-xs'
                      }`}>
                        {comment.author.username.charAt(0).toUpperCase()}
                      </div>
                    );
                  })()}
                </div>
                
                {/* コメント内容 */}
                <div className="flex-1">
                  <div className={`bg-gray-100 rounded-lg px-2 py-1 ${compact ? 'px-2 py-1' : 'px-3 py-2'}`}>
                    <div className="flex items-center justify-between mb-1">
                      <Link
                        href={`/profile/${comment.author.username}`}
                        className={`font-medium text-gray-900 hover:text-blue-600 transition-colors no-underline hover:no-underline ${
                          compact ? 'text-xs' : 'text-sm'
                        }`}
                      >
                        {comment.author.username}
                      </Link>
                      <span className={compact ? "text-xs text-gray-500" : "text-xs text-gray-500"}>
                        {formatDate(comment.createdAt)}
                      </span>
                    </div>
                    <p className={`text-gray-800 whitespace-pre-wrap ${compact ? 'text-xs' : 'text-sm'}`}>
                      {comment.content}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}