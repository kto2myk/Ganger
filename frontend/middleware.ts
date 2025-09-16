// NextAuth v5 の auth() をそのまま middleware としてエクスポートする形に変更
// これにより Cookie 名の変化や JWT/DB セッション方式の差異を気にせず保護できる
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { getToken } from 'next-auth/jwt';

// Edge 環境対応。auth() ではなく getToken を使って JWT を復号しセッション判定
export async function middleware(req: NextRequest) {
  const protectedMatchers = ['/post/create'];
  const { pathname } = req.nextUrl;
  if (!protectedMatchers.some(p => pathname.startsWith(p))) return NextResponse.next();

  // secret を明示指定 (v5 beta で MissingSecret 回避 & 署名一貫性確保)
  const secret = process.env.AUTH_SECRET || process.env.NEXTAUTH_SECRET || 'dev-fallback-static-secret';
  const token = await (getToken as any)({ req, secret });
  if (!token) {
    const loginUrl = new URL('/login', req.url);
    loginUrl.searchParams.set('next', pathname);
    return NextResponse.redirect(loginUrl);
  }
  return NextResponse.next();
}

export const config = { matcher: ['/post/create'] };