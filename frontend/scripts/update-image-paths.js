const { PrismaClient } = require('@prisma/client');
const prisma = new PrismaClient();

async function updateImagePaths() {
  console.log('=== 画像パス更新スクリプト ===');
  
  try {
    // 現在の画像パスを取得
    const images = await prisma.postImage.findMany();
    console.log(`📋 ${images.length}件の画像を確認中...`);
    
    let updatedCount = 0;
    
    for (const image of images) {
      // 既存のパスが /uploads/legacy/ で始まっている場合はスキップ
      if (image.url.startsWith('/uploads/legacy/')) {
        console.log(`✅ 既に更新済み: ${image.url}`);
        continue;
      }
      
      // レガシーパスから新しいパスへの変換
      let newPath = image.url;
      
      // Gangerフォルダーのパスパターンを変換
      if (image.url.includes('post_images/')) {
        const filename = image.url.split('/').pop();
        newPath = `/uploads/legacy/${filename}`;
      } 
      // 相対パスの場合
      else if (!image.url.startsWith('/')) {
        newPath = `/uploads/legacy/${image.url}`;
      }
      // その他のパスも legacy フォルダーに移動
      else {
        const filename = image.url.split('/').pop();
        newPath = `/uploads/legacy/${filename}`;
      }
      
      // パスを更新
      if (newPath !== image.url) {
        await prisma.postImage.update({
          where: { id: image.id },
          data: { url: newPath }
        });
        
        console.log(`🔄 更新: ${image.url} → ${newPath}`);
        updatedCount++;
      }
    }
    
    console.log(`\n✅ 画像パス更新完了: ${updatedCount}件`);
    
  } catch (error) {
    console.error('❌ 画像パス更新エラー:', error);
    throw error;
  } finally {
    await prisma.$disconnect();
  }
}

// スクリプト実行
updateImagePaths()
  .then(() => {
    console.log('🎉 画像パス更新スクリプトが正常に完了しました');
    process.exit(0);
  })
  .catch((error) => {
    console.error('❌ 画像パス更新スクリプトでエラーが発生しました:', error);
    process.exit(1);
  });