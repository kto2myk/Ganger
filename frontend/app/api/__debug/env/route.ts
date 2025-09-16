import { NextResponse } from 'next/server';

export const runtime = 'nodejs';

export function GET() {
  return NextResponse.json({
    has_DATABASE_URL: !!process.env.DATABASE_URL,
    DATABASE_URL_sample: process.env.DATABASE_URL?.slice(0,20),
    has_NEXTAUTH_SECRET: !!process.env.NEXTAUTH_SECRET,
    has_AUTH_SECRET: !!process.env.AUTH_SECRET
  });
}