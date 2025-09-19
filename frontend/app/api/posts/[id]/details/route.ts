import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '../../../../../lib/prisma';

export async function GET(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const post = await prisma.post.findUnique({
      where: { id: params.id },
      include: {
        author: {
          select: {
            id: true,
            username: true,
            email: true,
            image: true,
            profileImage: true,
            bio: true,
            createdAt: true
          }
        },
        images: {
          orderBy: { order: 'asc' }
        },
        tags: true,
        likes: {
          include: {
            user: {
              select: {
                id: true,
                username: true
              }
            }
          }
        },
        comments: {
          include: {
            author: {
              select: {
                id: true,
                username: true,
                image: true,
                profileImage: true
              }
            }
          },
          orderBy: { createdAt: 'desc' }
        },
        reposts: {
          include: {
            user: {
              select: {
                id: true,
                username: true
              }
            }
          }
        },
        _count: {
          select: {
            likes: true,
            comments: true,
            reposts: true
          }
        }
      }
    });

    if (!post) {
      return NextResponse.json({ error: 'Post not found' }, { status: 404 });
    }

    return NextResponse.json({ post });
  } catch (error) {
    console.error('投稿詳細取得エラー:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}