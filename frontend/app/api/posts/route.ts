import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';
import { prisma } from '../../../lib/prisma';

const createPostSchema = z.object({
  content: z.string().min(1).max(5000),
  tags: z.array(z.string()).optional(),
  images: z.array(z.string().url()).optional()
});

export async function GET() {
  const posts = await prisma.post.findMany({
    take: 20,
    orderBy: { createdAt: 'desc' },
    include: { author: true, images: true, tags: true, likes: true }
  });
  return NextResponse.json({ posts });
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const parsed = createPostSchema.parse(body);
    // TODO: 認証ユーザーID取得 (仮置き)
    const userId = body.userId || 'demo-user';

    const post = await prisma.post.create({
      data: {
        content: parsed.content,
        authorId: userId,
        tags: parsed.tags?.map(tag => ({ tag })) || [],
        images: parsed.images?.map((url, i) => ({ url, order: i })) || []
      }
    });
    return NextResponse.json({ post }, { status: 201 });
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 400 });
  }
}
