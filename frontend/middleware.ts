import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// 簡易保護: ログイン必須パス
const protectedPrefixes = ['/post/create'];

export function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;
  if (protectedPrefixes.some(p => pathname.startsWith(p))) {
    const hasSessionToken = req.cookies.get('authjs.session-token') || req.cookies.get('__Secure-authjs.session-token');
    if (!hasSessionToken) {
      const loginUrl = new URL('/login', req.url);
      loginUrl.searchParams.set('next', pathname);
      return NextResponse.redirect(loginUrl);
    }
  }
  return NextResponse.next();
}

export const config = {
  matcher: ['/post/create']
};