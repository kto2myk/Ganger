import { NextRequest, NextResponse } from 'next/server';
import { getToken } from 'next-auth/jwt';

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  console.log(`[middleware] Request to: ${pathname}`);
  
  // 認証が必要なパスを定義
  const protectedPaths = ['/home', '/post/create', '/me', '/profile', '/messages'];
  
  const isProtectedPath = protectedPaths.some(path => 
    pathname.startsWith(path)
  );
  
  if (!isProtectedPath) {
    console.log(`[middleware] Public path, allowing access: ${pathname}`);
    return NextResponse.next();
  }
  
  console.log(`[middleware] Checking authentication for protected path: ${pathname}`);
  
  try {
    const token = await getToken({ 
      req: request,
      secret: process.env.AUTH_SECRET || process.env.NEXTAUTH_SECRET || 'my-super-secret-key-32-characters-long-stable-secret-2024',
      salt: 'authjs.session-token'
    });
    
    if (token) {
      console.log(`[middleware] Valid session found for user: ${token.email}`);
      return NextResponse.next();
    }
    
    // セッションが無効な場合
    console.log(`[middleware] No valid session found, redirecting to login`);
    const loginUrl = new URL('/login', request.url);
    loginUrl.searchParams.set('next', pathname);
    loginUrl.searchParams.set('expired', 'true');
    
    return NextResponse.redirect(loginUrl);
    
  } catch (error) {
    console.error(`[middleware] Error checking session:`, error);
    
    // トークン取得エラーの場合もログインページにリダイレクト
    const loginUrl = new URL('/login', request.url);
    loginUrl.searchParams.set('next', pathname);
    loginUrl.searchParams.set('error', 'session_check_failed');
    
    return NextResponse.redirect(loginUrl);
  }
}

export const config = {
  matcher: [
    '/((?!api|_next/static|_next/image|favicon.ico|uploads).*)',
  ],
};