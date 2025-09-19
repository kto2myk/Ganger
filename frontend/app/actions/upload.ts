'use server';

import { writeFile, mkdir } from 'fs/promises';
import { join } from 'path';
import { randomUUID } from 'crypto';

export async function uploadImage(formData: FormData) {
  try {
    const file = formData.get('file') as File;
    if (!file) {
      return { error: 'ファイルが選択されていません' };
    }

    // ファイル形式チェック
    if (!file.type.startsWith('image/')) {
      return { error: '画像ファイルのみアップロード可能です' };
    }

    // ファイルサイズチェック (5MB制限)
    if (file.size > 5 * 1024 * 1024) {
      return { error: 'ファイルサイズは5MB以下にしてください' };
    }

    const bytes = await file.arrayBuffer();
    const buffer = new Uint8Array(bytes);

    // アップロードディレクトリの作成
    const uploadDir = join(process.cwd(), 'public', 'uploads');
    try {
      await mkdir(uploadDir, { recursive: true });
    } catch (error) {
      // ディレクトリが既に存在する場合は無視
    }

    // ユニークなファイル名生成
    const extension = file.name.split('.').pop() || 'jpg';
    const filename = `${randomUUID()}.${extension}`;
    const filepath = join(uploadDir, filename);

    // ファイル保存
    await writeFile(filepath, buffer);

    return { 
      success: true, 
      url: `/uploads/${filename}`,
      filename: filename 
    };
  } catch (error) {
    console.error('Upload error:', error);
    return { error: 'アップロードに失敗しました' };
  }
}