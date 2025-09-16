"use client";
import { useState } from 'react';
import { signIn } from 'next-auth/react';
import { useRouter } from 'next/navigation';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true); setError(null);
    const res = await signIn('credentials', { email, password, redirect: false });
    setLoading(false);
    if (res?.error) { setError('ログイン失敗: ' + res.error); return; }
    router.push('/home');
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
