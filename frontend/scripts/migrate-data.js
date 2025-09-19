const { PrismaClient } = require('@prisma/client');
const sqlite3 = require('sqlite3').verbose();
const bcrypt = require('bcryptjs');
const path = require('path');
const fs = require('fs');

// Prismaクライアントの初期化
const prisma = new PrismaClient();

// 元のPythonアプリのデータベースパス
const oldDbPath = path.join(__dirname, '..', '..', 'Ganger', 'app', 'model', 'database_manager', 'Ganger.db');

console.log('=== Ganger データベース移行スクリプト ===');
console.log('元のデータベースパス:', oldDbPath);

async function migrateData() {
  console.log('\n🔄 データ移行を開始します...');

  return new Promise((resolve, reject) => {
    // 元のデータベースを読み取り専用で開く
    const oldDb = new sqlite3.Database(oldDbPath, sqlite3.OPEN_READONLY, (err) => {
      if (err) {
        reject(new Error(`元のデータベース接続エラー: ${err.message}`));
        return;
      }
      console.log('✅ 元のデータベースに接続しました');
    });

    let migratedData = {
      users: 0,
      posts: 0,
      images: 0,
      tags: 0,
      likes: 0,
      follows: 0
    };

    async function migrateUsers() {
      return new Promise((resolve, reject) => {
        console.log('\n👤 ユーザーデータを移行中...');
        
        oldDb.all('SELECT * FROM users', async (err, users) => {
          if (err) {
            reject(new Error(`ユーザーデータ取得エラー: ${err.message}`));
            return;
          }

          try {
            for (const user of users) {
              // パスワードをbcryptでハッシュ化（元のパスワードは使わず、一時的なパスワードを設定）
              const tempPassword = 'temp123'; // 一時パスワード
              const hashedPassword = await bcrypt.hash(tempPassword, 12);

              // 既存チェック（メールアドレスとユーザー名）
              const existingUser = await prisma.user.findFirst({
                where: {
                  OR: [
                    { email: user.email },
                    { username: user.username }
                  ]
                }
              });

              if (!existingUser) {
                await prisma.user.create({
                  data: {
                    username: user.username,
                    email: user.email,
                    passwordHash: hashedPassword,
                    bio: user.bio,
                    profileImage: user.profile_image,
                    createdAt: user.create_time ? new Date(user.create_time) : new Date()
                  }
                });
                migratedData.users++;
              } else {
                console.log(`⚠️  ユーザーが既に存在します: ${user.username} (${user.email})`);
              }
            }
            
            console.log(`✅ ユーザー移行完了: ${migratedData.users}件`);
            resolve();
          } catch (error) {
            reject(new Error(`ユーザー移行エラー: ${error.message}`));
          }
        });
      });
    }

    async function migrateTags() {
      return new Promise((resolve, reject) => {
        console.log('\n🏷️  タグデータを移行中...');
        console.log('ℹ️  現在のスキーマではPostTagテーブルでタグを管理します');
        console.log('✅ タグ移行完了: スキップ（PostTagで直接管理）');
        resolve();
      });
    }

    async function migratePosts() {
      return new Promise((resolve, reject) => {
        console.log('\n📝 投稿データを移行中...');
        
        // 投稿、画像、タグの関連データを結合して取得
        const query = `
          SELECT 
            p.*,
            u.email as user_email,
            GROUP_CONCAT(i.img_path) as image_paths,
            GROUP_CONCAT(tm.tag_text) as tag_texts
          FROM posts p
          JOIN users u ON p.user_id = u.id
          LEFT JOIN images i ON p.post_id = i.post_id
          LEFT JOIN tag_posts tp ON p.post_id = tp.post_id
          LEFT JOIN tag_master tm ON tp.tag_id = tm.tag_id
          GROUP BY p.post_id
          ORDER BY p.post_time DESC
        `;
        
        oldDb.all(query, async (err, posts) => {
          if (err) {
            reject(new Error(`投稿データ取得エラー: ${err.message}`));
            return;
          }

          try {
            for (const post of posts) {
              // ユーザーを取得
              const user = await prisma.user.findUnique({
                where: { email: post.user_email }
              });

              if (!user) {
                console.log(`⚠️  ユーザーが見つかりません: ${post.user_email}`);
                continue;
              }

              // 既存投稿チェック
              const existingPost = await prisma.post.findFirst({
                where: {
                  content: post.body_text,
                  authorId: user.id,
                  createdAt: post.post_time ? new Date(post.post_time) : undefined
                }
              });

              if (!existingPost) {
                // 投稿作成（replyToIdは現在のスキーマにないため無視）
                const newPost = await prisma.post.create({
                  data: {
                    content: post.body_text || '',
                    authorId: user.id,
                    createdAt: post.post_time ? new Date(post.post_time) : new Date(),
                  }
                });

                // 画像データ移行
                if (post.image_paths) {
                  const imagePaths = post.image_paths.split(',');
                  for (let i = 0; i < imagePaths.length; i++) {
                    const imagePath = imagePaths[i].trim();
                    if (imagePath) {
                      await prisma.postImage.create({
                        data: {
                          postId: newPost.id,
                          url: `/uploads/legacy/${imagePath}`,
                          order: i
                        }
                      });
                      migratedData.images++;
                    }
                  }
                }

                // タグデータ移行
                if (post.tag_texts) {
                  const tagTexts = post.tag_texts.split(',');
                  for (const tagText of tagTexts) {
                    const trimmedTag = tagText.trim();
                    if (trimmedTag) {
                      await prisma.postTag.create({
                        data: {
                          postId: newPost.id,
                          tag: trimmedTag
                        }
                      });
                    }
                  }
                }

                migratedData.posts++;
              }
            }
            
            console.log(`✅ 投稿移行完了: ${migratedData.posts}件`);
            console.log(`✅ 画像移行完了: ${migratedData.images}件`);
            resolve();
          } catch (error) {
            reject(new Error(`投稿移行エラー: ${error.message}`));
          }
        });
      });
    }

    async function migrateLikes() {
      return new Promise((resolve, reject) => {
        console.log('\n❤️  いいねデータを移行中...');
        
        const query = `
          SELECT 
            l.*,
            u.email as user_email,
            p.body_text
          FROM likes l
          JOIN users u ON l.user_id = u.id
          JOIN posts p ON l.post_id = p.post_id
        `;
        
        oldDb.all(query, async (err, likes) => {
          if (err) {
            reject(new Error(`いいねデータ取得エラー: ${err.message}`));
            return;
          }

          try {
            for (const like of likes) {
              // ユーザーを取得
              const user = await prisma.user.findUnique({
                where: { email: like.user_email }
              });

              if (!user) continue;

              // 投稿を取得（内容とタイムスタンプで検索）
              const post = await prisma.post.findFirst({
                where: {
                  content: like.body_text || ''
                }
              });

        if (post) {
          const existingLike = await prisma.like.findUnique({
            where: {
              userId_postId: {
                userId: user.id,
                postId: post.id
              }
            }
          });                if (!existingLike) {
                  await prisma.like.create({
                    data: {
                      postId: post.id,
                      userId: user.id,
                      createdAt: like.created_at ? new Date(like.created_at) : new Date()
                    }
                  });
                  migratedData.likes++;
                }
              }
            }
            
            console.log(`✅ いいね移行完了: ${migratedData.likes}件`);
            resolve();
          } catch (error) {
            reject(new Error(`いいね移行エラー: ${error.message}`));
          }
        });
      });
    }

    // 移行実行
    (async () => {
      try {
        await migrateUsers();
        await migrateTags();
        await migratePosts();
        await migrateLikes();

        console.log('\n🎉 データ移行が完了しました！');
        console.log('移行結果:');
        console.log(`- ユーザー: ${migratedData.users}件`);
        console.log(`- 投稿: ${migratedData.posts}件`);
        console.log(`- 画像: ${migratedData.images}件`);
        console.log(`- タグ: ${migratedData.tags}件`);
        console.log(`- いいね: ${migratedData.likes}件`);

        oldDb.close();
        await prisma.$disconnect();
        resolve(migratedData);
      } catch (error) {
        console.error('❌ データ移行エラー:', error.message);
        oldDb.close();
        await prisma.$disconnect();
        reject(error);
      }
    })();
  });
}

// スクリプト実行
if (require.main === module) {
  migrateData()
    .then((result) => {
      console.log('\n✅ 移行スクリプトが正常に完了しました');
      process.exit(0);
    })
    .catch((error) => {
      console.error('\n❌ 移行スクリプトでエラーが発生しました:', error.message);
      process.exit(1);
    });
}

module.exports = { migrateData };