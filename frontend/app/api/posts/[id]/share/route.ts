import { NextRequest, NextResponse } from 'next/server';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

/**
 * 投稿共有情報生成API（GET）
 * 指定された投稿の共有用データとURLを生成し、各ソーシャルメディア向けのリンクを作成
 * @param request - APIリクエスト（クエリパラメータ: type）
 * @param params - URLパラメータ（投稿ID）
 */
export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const { id: postId } = params;
    const { searchParams } = new URL(request.url);
    // 共有タイプの指定（link, twitter, facebook, line, all）
    const type = searchParams.get('type') || 'link';

    // 投稿が存在するか確認
    const post = await prisma.post.findUnique({
      where: { id: postId },
      include: {
        author: {
          select: {
            id: true,
            username: true,
            profileImage: true
          }
        },
        images: {
          select: { url: true },
          take: 1
        }
      }
    });

    if (!post) {
      return NextResponse.json({ error: 'Post not found' }, { status: 404 });
    }

    const baseUrl = process.env.NEXT_PUBLIC_BASE_URL || 'http://localhost:3000';
    const postUrl = `${baseUrl}/post/${postId}`;
    const shareText = `${post.author.username}さんの投稿: ${post.content.slice(0, 100)}${post.content.length > 100 ? '...' : ''}`;
    const imageUrl = post.images[0]?.url;

    // 各ソーシャルメディアプラットフォーム向けのURLを生成
    let shareUrls: Record<string, string> = {};

    switch (type) {
      case 'twitter':
        // Twitter投稿用URLを生成
        shareUrls.twitter = `https://twitter.com/intent/tweet?text=${encodeURIComponent(shareText)}&url=${encodeURIComponent(postUrl)}`;
        break;
      
      case 'facebook':
        // Facebookシェア用URLを生成
        shareUrls.facebook = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(postUrl)}`;
        break;
      
      case 'line':
        // LINEシェア用URLを生成
        shareUrls.line = `https://social-plugins.line.me/lineit/share?url=${encodeURIComponent(postUrl)}&text=${encodeURIComponent(shareText)}`;
        break;
      
      case 'all':
        // 全プラットフォームのURLを一括生成
        shareUrls = {
          twitter: `https://twitter.com/intent/tweet?text=${encodeURIComponent(shareText)}&url=${encodeURIComponent(postUrl)}`,
          facebook: `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(postUrl)}`,
          line: `https://social-plugins.line.me/lineit/share?url=${encodeURIComponent(postUrl)}&text=${encodeURIComponent(shareText)}`,
          copy: postUrl  // クリップボードコピー用
        };
        break;
      
      default:
        // デフォルトは単純なリンクコピー
        shareUrls.link = postUrl;
        break;
    }

    return NextResponse.json({
      success: true,
      post: {
        id: post.id,
        content: post.content,
        author: post.author,
        imageUrl
      },
      shareData: {
        url: postUrl,
        text: shareText,
        title: `${post.author.username}さんの投稿`,
        shareUrls
      }
    });

  } catch (error) {
    console.error('Error generating share data:', error);
    return NextResponse.json(
      { error: 'Internal server error' }, 
      { status: 500 }
    );
  }
}

// 共有カウンターログ（オプション）
export async function POST(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const { id: postId } = params;
    const body = await request.json();
    const { platform } = body; // twitter, facebook, line, copy

    // 投稿が存在するか確認
    const post = await prisma.post.findUnique({
      where: { id: postId },
      select: { id: true }
    });

    if (!post) {
      return NextResponse.json({ error: 'Post not found' }, { status: 404 });
    }

    // 共有ログを記録（将来的な分析のため）
    // ここでは単純に成功レスポンスを返す
    console.log(`Post ${postId} shared on ${platform}`);

    return NextResponse.json({ 
      success: true,
      message: 'Share logged successfully'
    });

  } catch (error) {
    console.error('Error logging share:', error);
    return NextResponse.json(
      { error: 'Internal server error' }, 
      { status: 500 }
    );
  }
}