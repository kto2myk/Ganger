// NextAuth v5 の auth() をそのまま middleware としてエクスポートする形に変更
// これにより Cookie 名の変化や JWT/DB セッション方式の差異を気にせず保護できる
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { auth } from './app/api/auth/[...nextauth]/route';

export async function middleware(req: NextRequest) {
  // 対象パスのみ判定
  const protectedMatchers = ['/post/create'];
  const { pathname } = req.nextUrl;
  if (!protectedMatchers.some(p => pathname.startsWith(p))) {
    return NextResponse.next();
  }

  const session = await auth();
  if (!session?.user) {
    const loginUrl = new URL('/login', req.url);
    loginUrl.searchParams.set('next', pathname);
    return NextResponse.redirect(loginUrl);
  }
  return NextResponse.next();
}

export const config = { matcher: ['/post/create'] };