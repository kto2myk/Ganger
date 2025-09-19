'use server';

import { prisma } from '../../lib/prisma';
import { auth } from '../api/auth/[...nextauth]/route';
import { redirect } from 'next/navigation';

export async function createPost(formData: FormData) {
  try {
    const session = await auth();
    if (!session?.user?.email) {
      return { error: 'ログインが必要です' };
    }

    const content = formData.get('content') as string;
    const images = formData.getAll('images') as string[];

    if (!content.trim() && images.length === 0) {
      return { error: '投稿内容または画像が必要です' };
    }

    // ユーザーを取得
    const user = await prisma.user.findUnique({
      where: { email: session.user.email }
    });

    if (!user) {
      return { error: 'ユーザーが見つかりません' };
    }

    // 投稿を作成
    const post = await prisma.post.create({
      data: {
        content: content.trim(),
        authorId: user.id,
        images: {
          create: images.map(url => ({ url }))
        }
      },
      include: {
        author: {
          select: {
            id: true,
            username: true
          }
        },
        images: true,
        tags: true,
        likes: true
      }
    });

    return { success: true, post };
  } catch (error) {
    console.error('Create post error:', error);
    return { error: '投稿の作成に失敗しました' };
  }
}