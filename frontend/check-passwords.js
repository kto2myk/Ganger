const { PrismaClient } = require('@prisma/client');
const bcrypt = require('bcryptjs');
const prisma = new PrismaClient();

async function checkTestUserPasswords() {
  try {
    // testuser と exampleuser のパスワードハッシュを取得
    const testUsers = await prisma.user.findMany({
      where: {
        OR: [
          { username: 'testuser' },
          { username: 'exampleuser' }
        ]
      },
      select: {
        id: true,
        username: true,
        email: true,
        passwordHash: true,
        createdAt: true
      }
    });
    
    console.log('=== テストユーザーのパスワード情報 ===');
    
    for (const user of testUsers) {
      console.log(`\nユーザー名: ${user.username}`);
      console.log(`Email: ${user.email}`);
      console.log(`作成日: ${user.createdAt.toLocaleDateString('ja-JP')}`);
      console.log(`パスワードハッシュ: ${user.passwordHash.substring(0, 20)}...`);
      
      // よくあるテストパスワードをチェック
      const commonPasswords = [
        'password',
        'test',
        'testtest',
        '123456',
        'password123',
        'test123',
        user.username, // ユーザー名と同じ
        user.email.split('@')[0], // emailのローカル部分
        '111111',
        'aaaaaa'
      ];
      
      console.log('一般的なパスワードをチェック中...');
      
      for (const pwd of commonPasswords) {
        try {
          const isMatch = await bcrypt.compare(pwd, user.passwordHash);
          if (isMatch) {
            console.log(`✅ パスワードが見つかりました: "${pwd}"`);
            break;
          }
        } catch (error) {
          // エラーが発生してもスキップ
        }
      }
    }
    
    // 念のため、全ユーザーで簡単なパスワードパターンもチェック
    console.log('\n=== 他のユーザーで "test" パスワードを使用しているアカウント ===');
    const allUsers = await prisma.user.findMany({
      select: {
        username: true,
        email: true,
        passwordHash: true
      },
      take: 10 // 最初の10人だけチェック
    });
    
    for (const user of allUsers) {
      try {
        const isTestPassword = await bcrypt.compare('test', user.passwordHash);
        if (isTestPassword) {
          console.log(`${user.username} (${user.email}) - パスワード: "test"`);
        }
      } catch (error) {
        // スキップ
      }
    }
    
  } catch (error) {
    console.error('Error:', error);
  } finally {
    await prisma.$disconnect();
  }
}

checkTestUserPasswords();