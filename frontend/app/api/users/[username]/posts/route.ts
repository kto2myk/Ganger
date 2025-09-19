import { NextRequest, NextResponse } from 'next/server';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

export async function GET(
  request: NextRequest,
  { params }: { params: { username: string } }
) {
  try {
    const { searchParams } = new URL(request.url);
    const cursor = searchParams.get('cursor');
    const limit = parseInt(searchParams.get('limit') || '10', 10);

    // ユーザーを検索
    const user = await prisma.user.findUnique({
      where: { username: params.username },
      select: { id: true }
    });

    if (!user) {
      return NextResponse.json({ error: 'User not found' }, { status: 404 });
    }

    // 投稿を取得（カーソルベースの無限スクロール対応）
    const posts = await prisma.post.findMany({
      where: {
        authorId: user.id
      },
      include: {
        author: {
          select: {
            id: true,
            username: true,
            image: true,
            profileImage: true
          }
        },
        images: {
          select: {
            id: true,
            url: true
          }
        },
        tags: {
          select: {
            id: true,
            tag: true
          }
        },
        likes: {
          select: {
            id: true,
            userId: true
          }
        },
        _count: {
          select: {
            comments: true,
            likes: true,
            reposts: true
          }
        }
      },
      orderBy: {
        createdAt: 'desc'
      },
      cursor: cursor ? { id: cursor } : undefined,
      skip: cursor ? 1 : 0,
      take: limit + 1 // 次のページがあるかチェック用
    });

    // 次のカーソルを設定
    const hasNextPage = posts.length > limit;
    const nextCursor = hasNextPage ? posts[limit - 1]?.id : null;

    // 余分な投稿を削除
    if (hasNextPage) {
      posts.pop();
    }

    // タグの構造を平坦化
    const formattedPosts = posts.map(post => ({
      ...post,
      tags: post.tags.map(pt => ({
        id: pt.id,
        name: pt.tag
      }))
    }));

    return NextResponse.json({
      posts: formattedPosts,
      nextCursor,
      hasNextPage
    });

  } catch (error) {
    console.error('Error fetching user posts:', error);
    return NextResponse.json(
      { error: 'Internal server error' }, 
      { status: 500 }
    );
  }
}