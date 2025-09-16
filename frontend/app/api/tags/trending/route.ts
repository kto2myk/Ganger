import { NextResponse } from 'next/server';

export async function GET() {
  // Placeholder trending tags (replace with DB ranking logic later)
  return NextResponse.json({ tags: ['fashion', 'design', 'dev', 'art', 'ganger'] });
}
