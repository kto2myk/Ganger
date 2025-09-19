import React, { useState, useEffect } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { Heart, MessageCircle, Share, X, Loader2, Repeat } from 'lucide-react';
import { PostDetailModal } from './PostDetailModal';

interface PostCardProps {
  post: any;
}

export function PostCard({ post }: PostCardProps) {
  // モーダル表示状態の管理
  const [showModal, setShowModal] = useState(false);
  const [detailPost, setDetailPost] = useState(null);
  const [loading, setLoading] = useState(false);
  
  // ソーシャル機能の状態管理（いいね、リポスト）
  const [liked, setLiked] = useState(false);
  const [likeCount, setLikeCount] = useState(post._count?.likes || 0);
  const [reposted, setReposted] = useState(false);
  const [repostCount, setRepostCount] = useState(post._count?.reposts || 0);

  /**
   * 投稿カード全体がクリックされた時の処理
   * リンクやボタン以外の部分をクリックした場合にモーダルを開く
   * @param e - マウスクリックイベント
   */
  const handlePostClick = (e: React.MouseEvent) => {
    // リンククリックやボタンクリックは除外
    if ((e.target as HTMLElement).closest('a, button')) {
      return;
    }
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
    setDetailPost(null);
  };

  /**
   * いいねボタンクリック時の処理
   * 現在のいいね状態に応じてAPI呼び出し（追加/削除）を実行
   * @param e - クリックイベント（親要素への伝播を防ぐ）
   */
  const handleLike = async (e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      // 現在のいいね状態に応じてHTTPメソッドを決定
      const method = liked ? 'DELETE' : 'POST';
      const response = await fetch(`/api/posts/${post.id}/like`, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'user-email': 'test@example.com' // テスト用の認証ヘッダー
        }
      });

      if (response.ok) {
        const data = await response.json();
        // UIの状態を即座に更新（楽観的更新）
        setLiked(!liked);
        setLikeCount(data.likeCount);
      }
    } catch (error) {
      console.error('いいねの処理に失敗しました:', error);
    }
  };

  const handleRepost = async (e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      const method = reposted ? 'DELETE' : 'POST';
      const response = await fetch(`/api/posts/${post.id}/repost`, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'user-email': 'test@example.com' // テスト用
        },
        body: method === 'POST' ? JSON.stringify({}) : undefined
      });

      if (response.ok) {
        const data = await response.json();
        setReposted(!reposted);
        setRepostCount(data.repostCount);
      } else {
        const errorData = await response.json();
        console.error('リポストエラー:', errorData);
        if (errorData.error === 'Cannot repost your own post') {
          alert('自分の投稿はリポストできません');
        }
      }
    } catch (error) {
      console.error('リポストの処理に失敗しました:', error);
    }
  };

  const handleShare = async (e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      const response = await fetch(`/api/posts/${post.id}/share?type=all`);
      if (response.ok) {
        const data = await response.json();
        
        // Web Share API が利用可能な場合
        if (navigator.share) {
          await navigator.share({
            title: data.shareData.title,
            text: data.shareData.text,
            url: data.shareData.url
          });
        } else {
          // フォールバック: URLをクリップボードにコピー
          await navigator.clipboard.writeText(data.shareData.url);
          alert('投稿のURLをクリップボードにコピーしました！');
        }
      }
    } catch (error) {
      console.error('共有の処理に失敗しました:', error);
    }
  };

  const handleComment = (e: React.MouseEvent) => {
    e.stopPropagation();
    setShowModal(true);
  };

  /**
   * プロフィール画像のパスを適切な形式に変換する関数
   * 相対パス、絶対パス、URLを統一的に処理
   * @param imagePath - 元の画像パス（null可）
   * @returns 処理済みの画像パスまたはデフォルト画像
   */
  const getProfileImageSrc = (imagePath: string | null) => {
    if (!imagePath) return '/default-profile.svg';
    if (imagePath.startsWith('http')) return imagePath;
    if (imagePath.startsWith('/')) return imagePath;
    return `/${imagePath}`;
  };

  useEffect(() => {
    if (showModal && !detailPost) {
      const fetchPostDetails = async () => {
        setLoading(true);
        try {
          const response = await fetch(`/api/posts/${post.id}/details`);
          if (response.ok) {
            const data = await response.json();
            setDetailPost(data.post);
          }
        } catch (error) {
          console.error('投稿詳細の取得に失敗しました:', error);
        } finally {
          setLoading(false);
        }
      };

      fetchPostDetails();
    }
  }, [showModal, post.id, detailPost]);

  return (
    <>
      <article 
        className="rounded-xl border bg-white/70 backdrop-blur-sm shadow-sm p-4 flex flex-col gap-3 hover:shadow-md transition-shadow cursor-pointer"
        onClick={handlePostClick}
      >
        <header className="flex items-start gap-3">
          <Link 
            href={`/profile/${post.author?.username || ''}`}
            className="size-10 rounded-full bg-gradient-to-br from-indigo-400 to-indigo-600 text-white flex items-center justify-center text-sm font-semibold hover:from-indigo-500 hover:to-indigo-700 transition-colors no-underline hover:no-underline"
            onClick={(e) => e.stopPropagation()}
          >
            {post.author?.username?.[0]?.toUpperCase() || 'U'}
          </Link>
          <div className="flex flex-col text-sm">
            <Link
              href={`/profile/${post.author?.username || ''}`}
              className="font-medium text-neutral-800 hover:text-blue-600 transition-colors no-underline hover:no-underline"
              onClick={(e) => e.stopPropagation()}
            >
              {post.author?.username || 'Unknown User'}
            </Link>
            <span className="text-neutral-500 text-xs">{new Date(post.createdAt || Date.now()).toLocaleString()}</span>
          </div>
        </header>
        
        <div className="text-sm leading-relaxed whitespace-pre-wrap break-words hover:text-gray-700 transition-colors">
          {post.content}
        </div>
        {post.images && post.images.length > 0 && (
          <div className="grid gap-2 mt-3" style={{ gridTemplateColumns: `repeat(${Math.min(post.images.length, 3)}, 1fr)` }}>
            {post.images.slice(0, 6).map((img: any) => (
              <div key={img.id} className="relative aspect-[4/3] overflow-hidden rounded-lg bg-neutral-200">
                <Image src={img.url} alt="post image" fill className="object-cover" />
              </div>
            ))}
          </div>
        )}
        
        <footer className="flex items-center gap-4 pt-1 text-xs text-neutral-600">
          <button 
            className={`flex items-center gap-1 hover:text-red-500 transition-colors ${liked ? 'text-red-500' : ''}`}
            onClick={handleLike}
          >
            <Heart className={`w-4 h-4 ${liked ? 'fill-current' : ''}`} />
            <span>{likeCount}</span>
          </button>
          <button 
            className="flex items-center gap-1 hover:text-blue-500 transition-colors"
            onClick={handleComment}
          >
            <MessageCircle className="w-4 h-4" />
            <span>{post._count?.comments || 0}</span>
          </button>
          <button 
            className={`flex items-center gap-1 hover:text-green-500 transition-colors ${reposted ? 'text-green-500' : ''}`}
            onClick={handleRepost}
          >
            <Repeat className={`w-4 h-4 ${reposted ? 'fill-current' : ''}`} />
            <span>{repostCount}</span>
          </button>
          <button 
            className="flex items-center gap-1 hover:text-purple-500 transition-colors"
            onClick={handleShare}
          >
            <Share className="w-4 h-4" />
          </button>
        </footer>
      </article>

      {/* クライアントサイドモーダル */}
      {showModal && (
        <div 
          className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
          onClick={(e) => e.target === e.currentTarget && closeModal()}
        >
          <div className="relative bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
            <button
              onClick={closeModal}
              className="absolute top-4 right-4 z-50 bg-black/20 hover:bg-black/40 text-white rounded-full p-2 transition-colors"
              aria-label="モーダルを閉じる"
            >
              <X className="w-5 h-5" />
            </button>
            
            <div className="overflow-y-auto max-h-[90vh]">
              {loading ? (
                <div className="flex items-center justify-center p-8">
                  <Loader2 className="w-8 h-8 animate-spin text-gray-500" />
                  <span className="ml-2 text-gray-500">読み込み中...</span>
                </div>
              ) : detailPost ? (
                <PostDetailModal post={detailPost} />
              ) : (
                <div className="flex items-center justify-center p-8">
                  <span className="text-gray-500">投稿の読み込みに失敗しました</span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
