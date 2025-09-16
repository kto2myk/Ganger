import NextAuth from 'next-auth';
import Credentials from 'next-auth/providers/credentials';
import { prisma } from '../../../../lib/prisma';
import bcrypt from 'bcryptjs';
import { z } from 'zod';

// v5 beta 仕様: NextAuth() はハンドラオブジェクトを返す
// 旧 v4 のように関数をそのまま export しない

export const runtime = 'nodejs';

const credentialsSchema = z.object({
  email: z.string().email(),
  password: z.string().min(6)
});

// Secret 解決: 環境変数が無い (開発時の良くあるミス) でもクラッシュしないようフォールバック
// ※ dev 環境のみ自動生成。prod で未設定なら警告を出す (本番は必須)
// Stable dev fallback secret (avoid regenerating per import)
let resolvedSecret = process.env.AUTH_SECRET || process.env.NEXTAUTH_SECRET;
const g = globalThis as any;
if (!resolvedSecret) {
  if (!g.__DEV_AUTH_SECRET) {
    if (process.env.NODE_ENV === 'production') {
      console.error('[auth] FATAL: AUTH_SECRET / NEXTAUTH_SECRET 未設定');
      g.__DEV_AUTH_SECRET = 'PLEASE_SET_AUTH_SECRET_BEFORE_DEPLOY';
    } else {
      const rand = (g.crypto?.randomUUID?.() || Math.random().toString(36).slice(2)).replace(/-/g,'');
      g.__DEV_AUTH_SECRET = 'dev-fallback-' + rand;
      console.warn('[auth] 開発フォールバック secret を生成 (安定再利用)');
    }
  }
  resolvedSecret = g.__DEV_AUTH_SECRET;
}

export const {
  handlers: { GET, POST },
  auth,
  signIn,
  signOut
} = NextAuth({
  secret: resolvedSecret,
  trustHost: true,
  session: { strategy: 'jwt' },
  providers: [
    Credentials({
      name: 'Credentials',
      credentials: {
        email: { label: 'Email', type: 'text' },
        password: { label: 'Password', type: 'password' }
      },
      async authorize(raw) {
        if (!process.env.DATABASE_URL) {
          console.error('[auth] authorize: DATABASE_URL missing');
          return null; // surface as generic login failure
        }
        if (process.env.DATABASE_URL && process.env.NODE_ENV !== 'production') {
          console.log('[auth] authorize sees DATABASE_URL:', process.env.DATABASE_URL.slice(0,40));
        }
        const parsed = credentialsSchema.safeParse(raw);
        if (!parsed.success) return null;
        const { email, password } = parsed.data;
        const user = await prisma.user.findUnique({ where: { email } });
        if (!user) return null;
        const ok = await bcrypt.compare(password, user.passwordHash);
        if (!ok) return null;
        return { id: user.id, email: user.email, name: user.username } as any;
      }
    })
  ],
  callbacks: {
    async jwt({ token, user }: any) {
      if (user) token.id = user.id;
      return token;
    },
    async session({ session, token }: any) {
      if (token && session.user) (session.user as any).id = token.id;
      return session;
    }
  }
});
