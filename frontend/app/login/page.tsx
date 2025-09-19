"use client";
import { useState, useEffect } from 'react';
import { signIn } from 'next-auth/react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useRedirectIfAuth } from '@/lib/useAuthRedirect';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const searchParams = useSearchParams();
  
  // 認証済みの場合はホームにリダイレクト
  const { isLoading } = useRedirectIfAuth();

  useEffect(() => {
    // URL パラメータから状態を取得
    const expired = searchParams.get('expired');
    const errorParam = searchParams.get('error');
    
    if (expired === 'true') {
      setError('セッションが期限切れになりました。再度ログインしてください。');
    } else if (errorParam === 'session_check_failed') {
      setError('セッションの確認に失敗しました。再度ログインしてください。');
    }

    // ローカルストレージからセッション切れフラグを確認
    if (typeof window !== 'undefined') {
      const sessionExpired = localStorage.getItem('sessionExpired');
      if (sessionExpired === 'true') {
        setError('セッションが期限切れになりました。再度ログインしてください。');
        localStorage.removeItem('sessionExpired'); // フラグをクリア
      }
    }
  }, [searchParams]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true); 
    setError(null);
    
    const res = await signIn('credentials', { 
      email, 
      password, 
      redirect: false,
      callbackUrl: searchParams.get('next') || '/home'
    });
    
    setLoading(false);
    
    if (res?.error) { 
      setError('ログイン失敗: ' + res.error); 
      return; 
    }
    
    // ログイン成功時のリダイレクト
    const redirectTo = searchParams.get('next') || '/home';
    router.push(redirectTo);
  }

  // 認証チェック中はローディング表示
  if (isLoading) {
    return (
      <div className="max-w-sm mx-auto mt-10 bg-white/70 backdrop-blur-sm p-6 rounded-xl border text-center">
        <div className="text-sm text-neutral-500">読み込み中...</div>
      </div>
    );
  }

  return (
    <div className="max-w-sm mx-auto mt-10 bg-white/70 backdrop-blur-sm p-6 rounded-xl border">
      <h1 className="text-lg font-semibold mb-4">ログイン</h1>
      <form onSubmit={onSubmit} className="flex flex-col gap-4">
        <div className="flex flex-col gap-1">
          <label className="text-sm font-medium">Email</label>
          <input value={email} onChange={e=>setEmail(e.target.value)} type="email" required className="rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-sm font-medium">Password</label>
          <input value={password} onChange={e=>setPassword(e.target.value)} type="password" required className="rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
        </div>
        {error && <div className="text-xs text-red-600 whitespace-pre-wrap">{error}</div>}
        <button disabled={loading} className="px-4 py-2 rounded-md bg-indigo-600 text-white text-sm font-medium hover:bg-indigo-700 disabled:opacity-50">
          {loading ? '送信中...' : 'ログイン'}
        </button>
      </form>
      <p className="mt-4 text-xs text-neutral-500">まだアカウントが無い? <a href="/signup" className="underline">サインアップ</a></p>
    </div>
  );
}
