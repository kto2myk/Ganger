const { PrismaClient } = require('@prisma/client');
const prisma = new PrismaClient();

async function checkTestAccounts() {
  try {
    console.log('=== データベース内のユーザーアカウント ===');
    
    const users = await prisma.user.findMany({
      select: {
        id: true,
        username: true,
        email: true,
        realName: true,
        createdAt: true,
        profileImage: true,
        posts: {
          select: {
            id: true
          }
        }
      },
      orderBy: {
        createdAt: 'asc'
      }
    });
    
    users.forEach((user, index) => {
      console.log(`${index + 1}. ユーザー名: ${user.username}`);
      console.log(`   Email: ${user.email}`);
      console.log(`   名前: ${user.realName || 'なし'}`);
      console.log(`   作成日: ${user.createdAt.toLocaleDateString('ja-JP')}`);
      console.log(`   プロフィール画像: ${user.profileImage || 'なし'}`);
      console.log(`   投稿数: ${user.posts.length}`);
      console.log('---');
    });
    
    console.log(`\n総ユーザー数: ${users.length}`);
    
    // テスト系のアカウントを特定
    const testUsers = users.filter(user => 
      user.username.toLowerCase().includes('test') || 
      user.email.toLowerCase().includes('test') ||
      user.username.toLowerCase().includes('example') ||
      user.email.toLowerCase().includes('example')
    );
    
    if (testUsers.length > 0) {
      console.log('\n=== テスト系アカウント ===');
      testUsers.forEach(user => {
        console.log(`ユーザー名: ${user.username}`);
        console.log(`Email: ${user.email}`);
        console.log(`投稿数: ${user.posts.length}`);
        console.log('---');
      });
    }
    
  } catch (error) {
    console.error('Error:', error);
  } finally {
    await prisma.$disconnect();
  }
}

checkTestAccounts();