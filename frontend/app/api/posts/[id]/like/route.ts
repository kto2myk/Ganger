import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';

/**
 * 簡易的な認証チェック関数（実際のプロジェクトではNextAuthを使用）
 * リクエストヘッダーからユーザー情報を取得し、存在しない場合はテストユーザーを作成
 * @param request - Next.js APIリクエストオブジェクト
 * @returns ユーザー情報またはnull
 */
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

    // 投稿が存在するか確認
    const post = await prisma.post.findUnique({
      where: { id: postId },
      select: { id: true }
    });

    if (!post) {
      return NextResponse.json({ error: 'Post not found' }, { status: 404 });
    }

    // 既にいいねしているか確認
    const existingLike = await prisma.like.findUnique({
      where: {
        userId_postId: {
          userId: user.id,
          postId: postId
        }
      }
    });

    if (existingLike) {
      return NextResponse.json({ error: 'Already liked' }, { status: 400 });
    }

    // いいねを追加
    const like = await prisma.like.create({
      data: {
        userId: user.id,
        postId: postId
      }
    });

    // いいね数を取得
    const likeCount = await prisma.like.count({
      where: { postId: postId }
    });

    return NextResponse.json({ 
      success: true, 
      likeId: like.id,
      likeCount 
    });

  } catch (error) {
    console.error('Error creating like:', error);
    return NextResponse.json(
      { error: 'Internal server error' }, 
      { status: 500 }
    );
  }
}

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

    // いいねを削除
    const deletedLike = await prisma.like.deleteMany({
      where: {
        userId: user.id,
        postId: postId
      }
    });

    if (deletedLike.count === 0) {
      return NextResponse.json({ error: 'Like not found' }, { status: 404 });
    }

    // いいね数を取得
    const likeCount = await prisma.like.count({
      where: { postId: postId }
    });

    return NextResponse.json({ 
      success: true,
      likeCount 
    });

  } catch (error) {
    console.error('Error deleting like:', error);
    return NextResponse.json(
      { error: 'Internal server error' }, 
      { status: 500 }
    );
  }
}