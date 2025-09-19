import { NextResponse } from 'next/server';
import { auth } from '../../auth/[...nextauth]/route';
import { headers } from 'next/headers';

export const runtime = 'nodejs';

export async function GET() {
  try {
    const session = await auth();
    const h = headers();
    
    // Cookie情報を取得
    const cookieHeader = h.get('cookie') || '';
    const cookies = cookieHeader.split(';').map(c => c.trim()).filter(c => c.includes('auth'));
    
    return NextResponse.json({
      session: session,
      hasSession: !!session,
      user: session?.user || null,
      cookies: cookies,
      allHeaders: Object.fromEntries(h.entries()),
      timestamp: new Date().toISOString()
    });
  } catch (error: any) {
    return NextResponse.json({
      error: error?.message || 'Unknown error',
      session: null,
      hasSession: false
    }, { status: 500 });
  }
}
