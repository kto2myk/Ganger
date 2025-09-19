import { notFound } from 'next/navigation';
import { PrismaClient } from '@prisma/client';
import { ProfileDetail } from '@/components/profile/ProfileDetail';

const prisma = new PrismaClient();

interface ProfilePageProps {
  params: { username: string };
}

export default async function ProfilePage({ params }: ProfilePageProps) {
  const { username } = params;

  try {
    // ユーザー情報を取得
    const user = await prisma.user.findUnique({
      where: { username },
      select: {
        id: true,
        username: true,
        email: true,
        realName: true,
        bio: true,
        address: true,
        image: true,
        profileImage: true,
        createdAt: true,
        _count: {
          select: {
            posts: true,
            followers: true,
            following: true
          }
        }
      }
    });

    if (!user) {
      notFound();
    }

    // 初期投稿を取得（最初の10件）
    const initialPosts = await prisma.post.findMany({
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
      take: 11 // 次のページがあるかチェック用
    });

    // 次のカーソルを設定
    const hasNextPage = initialPosts.length > 10;
    const nextCursor = hasNextPage ? initialPosts[9]?.id : null;

    // 余分な投稿を削除
    if (hasNextPage) {
      initialPosts.pop();
    }

    // タグの構造を平坦化
    const formattedPosts = initialPosts.map(post => ({
      ...post,
      tags: post.tags.map(pt => ({
        id: pt.id,
        name: pt.tag
      }))
    }));

    return (
      <ProfileDetail 
        user={user}
        initialPosts={formattedPosts}
        initialNextCursor={nextCursor}
      />
    );

  } catch (error) {
    console.error('Profile page error:', error);
    notFound();
  }
}

// ページタイトルの動的生成
export async function generateMetadata({ params }: ProfilePageProps) {
  const { username } = params;

  try {
    const user = await prisma.user.findUnique({
      where: { username },
      select: {
        username: true,
        realName: true,
        bio: true
      }
    });

    if (!user) {
      return {
        title: 'ユーザーが見つかりません',
      };
    }

    return {
      title: `${user.realName || user.username} (@${user.username}) | Ganger`,
      description: user.bio || `${user.username}のプロフィールページ`,
    };
  } catch (error) {
    return {
      title: 'プロフィール | Ganger',
    };
  }
}
