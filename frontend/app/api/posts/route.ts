import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';
import { prisma } from '../../../lib/prisma';
import { auth } from '../auth/[...nextauth]/route';

export const runtime = 'nodejs';

const createPostSchema = z.object({
  content: z.string().min(1).max(5000),
  tags: z.array(z.string()).optional(),
  images: z.array(z.string().url()).optional()
});

export async function GET(req: NextRequest) {
  const cursor = req.nextUrl.searchParams.get('cursor');
  const take = 20;
  const posts = await prisma.post.findMany({
    take: take + 1,
    ...(cursor ? { cursor: { id: cursor }, skip: 1 } : {}),
    orderBy: { createdAt: 'desc' },
    include: { author: true, images: true, tags: true, likes: true }
  });
  let nextCursor: string | null = null;
  if (posts.length > take) {
    const next = posts.pop();
    nextCursor = next!.id;
  }
  return NextResponse.json({ posts, nextCursor });
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const parsed = createPostSchema.parse(body);
  const session = await auth();
  const userId = session?.user?.id as string | undefined;
  if (!userId) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

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
