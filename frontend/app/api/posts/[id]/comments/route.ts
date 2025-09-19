import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';

// 簡易的な認証チェック（実際のプロジェクトではNextAuthを使用）
async function getCurrentUser(request: NextRequest) {
  // TODO: 実際の認証実装
  // 現在はテスト用にヘッダーから user_email を取得
  const userEmail = request.headers.get('user-email') || 'test@example.com';
  
  // ユーザーが存在しない場合は作成
  let user = await prisma.user.findUnique({
    where: { email: userEmail },
    select: { id: true, email: true }
  });

  if (!user && userEmail === 'test@example.com') {
    // テストユーザーを作成
    user = await prisma.user.create({
      data: {
        email: userEmail,
        username: 'testuser',
        passwordHash: 'dummy' // テスト用
      },
      select: { id: true, email: true }
    });
  }
  
  return user;
}

/**
 * コメント一覧取得API（GET）
 * 指定された投稿のコメントをページネーション付きで取得
 * @param request - APIリクエスト（クエリパラメータ: page, limit）
 * @param params - URLパラメータ（投稿ID）
 */
export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const { id: postId } = params;
    const { searchParams } = new URL(request.url);
    // ページネーションパラメータの解析（デフォルト: 1ページ目、10件まで）
    const page = parseInt(searchParams.get('page') || '1');
    const limit = parseInt(searchParams.get('limit') || '10');
    const offset = (page - 1) * limit;

    // 投稿が存在するか確認
    const post = await prisma.post.findUnique({
      where: { id: postId },
      select: { id: true }
    });

    if (!post) {
      return NextResponse.json({ error: 'Post not found' }, { status: 404 });
    }

    const comments = await prisma.comment.findMany({
      where: { postId: postId },
      include: {
        author: {
          select: {
            id: true,
            username: true,
            profileImage: true
          }
        }
      },
      orderBy: { createdAt: 'desc' },
      skip: offset,
      take: limit
    });

    const totalComments = await prisma.comment.count({
      where: { postId: postId }
    });

    return NextResponse.json({
      comments,
      pagination: {
        page,
        limit,
        totalComments,
        hasMore: offset + limit < totalComments
      }
    });

  } catch (error) {
    console.error('Error fetching comments:', error);
    return NextResponse.json(
      { error: 'Internal server error' }, 
      { status: 500 }
    );
  }
}

// コメント投稿
export async function POST(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const user = await getCurrentUser(request);
    
    if (!user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const { id: postId } = params;
    const body = await request.json();
    const { content } = body;

    if (!content || typeof content !== 'string' || content.trim().length === 0) {
      return NextResponse.json({ error: 'Content is required' }, { status: 400 });
    }

    if (content.trim().length > 500) {
      return NextResponse.json({ error: 'Content too long (max 500 characters)' }, { status: 400 });
    }

    // 投稿が存在するか確認
    const post = await prisma.post.findUnique({
      where: { id: postId },
      select: { id: true }
    });

    if (!post) {
      return NextResponse.json({ error: 'Post not found' }, { status: 404 });
    }

    // コメントを作成
    const comment = await prisma.comment.create({
      data: {
        content: content.trim(),
        authorId: user.id,
        postId: postId
      },
      include: {
        author: {
          select: {
            id: true,
            username: true,
            profileImage: true
          }
        }
      }
    });

    return NextResponse.json({ 
      success: true, 
      comment 
    }, { status: 201 });

  } catch (error) {
    console.error('Error creating comment:', error);
    return NextResponse.json(
      { error: 'Internal server error' }, 
      { status: 500 }
    );
  }
}