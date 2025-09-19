'use client';

import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import { useEffect, useRef } from 'react';

export function SessionWatchdog() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const lastSessionCheck = useRef<string | null>(null);

  useEffect(() => {
    // ローディング中は何もしない
    if (status === 'loading') return;

    // セッション状態が変化した時の処理
    const currentSessionId = session?.user?.email || null;
    
    // 初回ロードまたはセッション状態変化を記録
    if (lastSessionCheck.current === null) {
      lastSessionCheck.current = currentSessionId;
      return;
    }

    // セッションが切れた場合（以前はあったが今はない）
    if (lastSessionCheck.current && !currentSessionId) {
      console.log('[SessionWatchdog] セッション期限切れを検知しました。ログインページにリダイレクトします。');
      
      // セッション切れを明示的にユーザーに通知
      if (typeof window !== 'undefined') {
        // ローカルストレージにセッション切れフラグを設定
        localStorage.setItem('sessionExpired', 'true');
      }
      
      router.push('/login?expired=true');
    }

    lastSessionCheck.current = currentSessionId;
  }, [session, status, router]);

  useEffect(() => {
    if (status === 'loading' || !session) return;

    // ブラウザ／タブを閉じる時の処理
    const handleBeforeUnload = (event: BeforeUnloadEvent) => {
      // セッションクリーンアップフラグを設定
      sessionStorage.setItem('browserClosing', 'true');
    };

    // ページが隠れた時（タブの切り替えや最小化）の処理
    const handleVisibilityChange = () => {
      if (document.hidden) {
        // ページが見えなくなった時刻を記録
        sessionStorage.setItem('lastHiddenTime', Date.now().toString());
      } else {
        // ページが再び見えるようになった時
        const lastHiddenTime = sessionStorage.getItem('lastHiddenTime');
        const browserClosing = sessionStorage.getItem('browserClosing');
        
        if (browserClosing === 'true') {
          // ブラウザが閉じられた可能性があるため、セッションを確認
          sessionStorage.removeItem('browserClosing');
          console.log('[SessionWatchdog] ブラウザ再開を検知、セッションを確認中...');
        }
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [session, status]);

  // 定期的なセッションチェック（1時間ごと - 1日の有効期限に合わせて頻度を下げる）
  useEffect(() => {
    if (status === 'loading' || !session) return;

    const intervalId = setInterval(async () => {
      try {
        const response = await fetch('/api/auth/session');
        const sessionData = await response.json();
        
        // セッションが無効になった場合
        if (!sessionData || !sessionData.user) {
          console.log('[SessionWatchdog] 定期チェックでセッション期限切れを検知しました。');
          
          if (typeof window !== 'undefined') {
            localStorage.setItem('sessionExpired', 'true');
          }
          
          router.push('/login?expired=true');
        }
      } catch (error) {
        console.error('[SessionWatchdog] セッションチェックエラー:', error);
        // エラーが続く場合はログインページに誘導
        router.push('/login?error=session_check_failed');
      }
    }, 60 * 60 * 1000); // 1時間ごと（1日有効期限なので頻度を下げる）

    return () => clearInterval(intervalId);
  }, [session, status, router]);

  return null; // このコンポーネントは何も表示しない
}