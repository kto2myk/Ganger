// シンプルなCookieベース認証チェック（Edge runtime対応）
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export async function middleware(req: NextRequest) {
  const protectedMatchers = ['/post/create'];
  const { pathname } = req.nextUrl;
  if (!protectedMatchers.some(p => pathname.startsWith(p))) {
    return NextResponse.next();
  }

  // NextAuth v5 のセッションCookieを直接確認
  // 可能性のあるCookie名をすべてチェック
  const sessionCookies = [
    'authjs.session-token',
    '__Secure-authjs.session-token',
    'next-auth.session-token',
    '__Secure-next-auth.session-token'
  ];
  
  const hasValidSession = sessionCookies.some(cookieName => {
    const cookie = req.cookies.get(cookieName);
    return cookie && cookie.value && cookie.value.length > 10;
  });

  if (!hasValidSession) {
    console.log('[middleware] No valid session cookie found, redirecting to login');
    console.log('[middleware] Available cookies:', req.cookies.getAll().map(c => c.name));
    const loginUrl = new URL('/login', req.url);
    loginUrl.searchParams.set('next', pathname);
    return NextResponse.redirect(loginUrl);
  }

  console.log('[middleware] Valid session found, allowing access to', pathname);
  return NextResponse.next();
}

export const config = { matcher: ['/post/create'] };