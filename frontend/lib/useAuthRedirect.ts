'use client';

import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

interface UseAuthRedirectOptions {
  redirectTo?: string;
  requireAuth?: boolean;
}

export function useAuthRedirect({ 
  redirectTo = '/login', 
  requireAuth = true 
}: UseAuthRedirectOptions = {}) {
  const { data: session, status } = useSession();
  const router = useRouter();

  useEffect(() => {
    // ローディング中は何もしない
    if (status === 'loading') return;

    // 認証が必要なページで未認証の場合
    if (requireAuth && !session) {
      console.log('[useAuthRedirect] セッションが切れています。ログインページにリダイレクトします。');
      router.push(redirectTo);
      return;
    }

    // 認証済みユーザーが認証不要ページ（ログイン、サインアップ）にアクセスした場合
    if (!requireAuth && session) {
      console.log('[useAuthRedirect] 認証済みユーザーです。ホームページにリダイレクトします。');
      router.push('/home');
      return;
    }
  }, [session, status, router, redirectTo, requireAuth]);

  return { session, status, isLoading: status === 'loading' };
}

export function useRequireAuth(redirectTo = '/login') {
  return useAuthRedirect({ redirectTo, requireAuth: true });
}

export function useRedirectIfAuth(redirectTo = '/home') {
  return useAuthRedirect({ redirectTo, requireAuth: false });
}