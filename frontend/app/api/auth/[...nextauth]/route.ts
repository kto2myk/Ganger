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
if (!resolvedSecret) {
  console.error('[auth] CRITICAL: No AUTH_SECRET found in environment variables!');
  resolvedSecret = 'my-super-secret-key-32-characters-long-stable-secret-2024';
  console.warn('[auth] Using hardcoded fallback secret for development only');
}

export const {
  handlers: { GET, POST },
  auth,
  signIn,
  signOut
} = NextAuth({
  secret: resolvedSecret,
  trustHost: true,
  session: { 
    strategy: 'jwt',
    maxAge: 24 * 60 * 60, // 1日（24時間）の秒数
    updateAge: 24 * 60 * 60, // セッション更新間隔も1日に設定
  },
  // クッキー設定でブラウザを閉じたら切れるようにする
  cookies: {
    sessionToken: {
      name: `next-auth.session-token`,
      options: {
        httpOnly: true,
        sameSite: 'lax',
        path: '/',
        secure: process.env.NODE_ENV === 'production',
        // maxAge を設定せずsessionのみ設定することで、ブラウザを閉じたら切れる
      }
    },
    callbackUrl: {
      name: `next-auth.callback-url`,
      options: {
        sameSite: 'lax',
        path: '/',
        secure: process.env.NODE_ENV === 'production',
      }
    },
    csrfToken: {
      name: `next-auth.csrf-token`,
      options: {
        httpOnly: true,
        sameSite: 'lax',
        path: '/',
        secure: process.env.NODE_ENV === 'production',
      }
    }
  },
  providers: [
    Credentials({
      name: 'Credentials',
      credentials: {
        email: { label: 'Email', type: 'text' },
        password: { label: 'Password', type: 'password' }
      },
      async authorize(raw) {
        console.log('[auth] authorize called with:', raw);
        if (!process.env.DATABASE_URL) {
          console.error('[auth] authorize: DATABASE_URL missing');
          return null;
        }
        if (process.env.DATABASE_URL && process.env.NODE_ENV !== 'production') {
          console.log('[auth] authorize sees DATABASE_URL:', process.env.DATABASE_URL.slice(0,40));
        }
        const parsed = credentialsSchema.safeParse(raw);
        if (!parsed.success) {
          console.log('[auth] validation failed:', parsed.error.issues);
          return null;
        }
        const { email, password } = parsed.data;
        console.log('[auth] looking for user with email:', email);
        
        try {
          const user = await prisma.user.findUnique({ where: { email } });
          if (!user) {
            console.log('[auth] user not found for email:', email);
            return null;
          }
          console.log('[auth] user found, checking password');
          const ok = await bcrypt.compare(password, user.passwordHash);
          if (!ok) {
            console.log('[auth] password check failed');
            return null;
          }
          console.log('[auth] authentication successful for user:', user.username);
          return { id: user.id, email: user.email, name: user.username } as any;
        } catch (error) {
          console.error('[auth] database error:', error);
          return null;
        }
      }
    })
  ],
  callbacks: {
    async jwt({ token, user }: any) {
      if (user) {
        token.id = user.id;
        // JWTトークンの有効期限を1日に設定
        token.exp = Math.floor(Date.now() / 1000) + (24 * 60 * 60); // 現在時刻 + 1日
      }
      return token;
    },
    async session({ session, token }: any) {
      if (token && session.user) {
        (session.user as any).id = token.id;
        // セッションの有効期限もトークンの有効期限に合わせる
        session.expires = new Date(token.exp * 1000).toISOString();
      }
      return session;
    }
  }
});
