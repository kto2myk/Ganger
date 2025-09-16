"use client";
import { useState } from 'react';

export default function SignupPage() {
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ok, setOk] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true); setError(null); setOk(false);
    const res = await fetch('/api/auth/signup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, username, password })
    });
    setLoading(false);
    if (!res.ok) {
      const j = await res.json().catch(()=>({error:'unknown'}));
      if (j.error === 'validation_error' && Array.isArray(j.issues)) {
        const msgs = j.issues.map((i:any)=>`${i.path.join('.')}: ${i.message}`).join('\n');
        setError(msgs);
      } else {
        setError(j.error || 'エラー');
      }
      return;
    }
    setOk(true);
  }

  return (
    <div className="max-w-sm mx-auto mt-10 bg-white/70 backdrop-blur-sm p-6 rounded-xl border">
      <h1 className="text-lg font-semibold mb-4">サインアップ</h1>
      <form onSubmit={onSubmit} className="flex flex-col gap-4">
        <div className="flex flex-col gap-1">
          <label className="text-sm font-medium">Email</label>
          <input value={email} onChange={e=>setEmail(e.target.value)} type="email" required placeholder="example@example.com" className="rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-sm font-medium">ユーザー名</label>
          <input value={username} onChange={e=>setUsername(e.target.value)} required className="rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-sm font-medium">パスワード</label>
          <input value={password} onChange={e=>setPassword(e.target.value)} type="password" required minLength={6} className="rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
        </div>
        {error && <div className="text-xs text-red-600 whitespace-pre-wrap">{error}</div>}
        {ok && <div className="text-xs text-green-600">作成完了。<a href="/login" className="underline">ログインへ</a></div>}
        <button disabled={loading} className="px-4 py-2 rounded-md bg-indigo-600 text-white text-sm font-medium hover:bg-indigo-700 disabled:opacity-50">
          {loading ? '送信中...' : '登録する'}
        </button>
      </form>
      <p className="mt-4 text-xs text-neutral-500">既にアカウントがありますか？ <a href="/login" className="underline">ログイン</a></p>
    </div>
  );
}
