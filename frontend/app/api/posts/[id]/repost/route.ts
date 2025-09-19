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
 * リポスト作成API（POST）
 * 指定された投稿をリポストし、リポスト数を返却
 * 自分の投稿はリポスト不可、重複リポストも禁止
 * @param request - APIリクエスト
 * @param params - URLパラメータ（投稿ID）
 */
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
    const { content } = body; // リポスト時のコメント（現在は未使用）

    // 投稿の存在確認と作者情報を取得
    const post = await prisma.post.findUnique({
      where: { id: postId },
      select: { id: true, authorId: true }
    });

    if (!post) {
      return NextResponse.json({ error: 'Post not found' }, { status: 404 });
    }

    // 自分の投稿はリポスト不可のビジネスルール
    if (post.authorId === user.id) {
      return NextResponse.json({ error: 'Cannot repost your own post' }, { status: 400 });
    }

    // 既にリポストしているか確認
    const existingRepost = await prisma.repost.findUnique({
      where: {
        userId_postId: {
          userId: user.id,
          postId: postId
        }
      }
    });

    if (existingRepost) {
      return NextResponse.json({ error: 'Already reposted' }, { status: 400 });
    }

    // リポストを作成
    const repost = await prisma.repost.create({
      data: {
        userId: user.id,
        postId: postId
      }
    });

    // リポスト数を取得
    const repostCount = await prisma.repost.count({
      where: { postId: postId }
    });

    return NextResponse.json({ 
      success: true, 
      repostId: repost.id,
      repostCount 
    });

  } catch (error) {
    console.error('Error creating repost:', error);
    return NextResponse.json(
      { error: 'Internal server error' }, 
      { status: 500 }
    );
  }
}

// リポスト削除
export async function DELETE(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const user = await getCurrentUser(request);
    
    if (!user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const { id: postId } = params;

    // リポストを削除
    const deletedRepost = await prisma.repost.deleteMany({
      where: {
        userId: user.id,
        postId: postId
      }
    });

    if (deletedRepost.count === 0) {
      return NextResponse.json({ error: 'Repost not found' }, { status: 404 });
    }

    // リポスト数を取得
    const repostCount = await prisma.repost.count({
      where: { postId: postId }
    });

    return NextResponse.json({ 
      success: true,
      repostCount 
    });

  } catch (error) {
    console.error('Error deleting repost:', error);
    return NextResponse.json(
      { error: 'Internal server error' }, 
      { status: 500 }
    );
  }
}