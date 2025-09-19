import { redirect } from 'next/navigation';
import { z } from 'zod';
import { prisma } from '../../../lib/prisma';
import { auth } from '../../api/auth/[...nextauth]/route';

const formSchema = z.object({
  content: z.string().min(1, '内容を入力してください').max(5000),
  tags: z.string().optional(), // comma separated
  images: z.string().optional() // newline separated URLs
});

async function createPost(formData: FormData) {
  'use server';
  const session = await auth();
  if (!session?.user?.id) {
    redirect('/login');
  }
  const raw = {
    content: formData.get('content')?.toString() || '',
    tags: formData.get('tags')?.toString(),
    images: formData.get('images')?.toString()
  };
  const parsed = formSchema.safeParse(raw);
  if (!parsed.success) {
    return { ok: false, errors: parsed.error.flatten().fieldErrors };
  }
  const tagArray = (parsed.data.tags || '')
    .split(',')
    .map(s => s.trim())
    .filter(Boolean);
  const imageArray = (parsed.data.images || '')
    .split(/\n|,/)
    .map(s => s.trim())
    .filter(Boolean);

  await prisma.post.create({
    data: {
      content: parsed.data.content,
      authorId: session.user.id as string,
      tags: {
        create: tagArray.map(t => ({ tag: t }))
      },
      images: {
        create: imageArray.map((u, i) => ({ url: u, order: i }))
      }
    }
  });
  redirect('/home');
}

export default function CreatePostPage() {
  return (
    <div className="max-w-2xl">
      <h1 className="text-xl font-semibold mb-4">投稿作成</h1>
      <form action={createPost} className="flex flex-col gap-4 bg-white/70 backdrop-blur-sm p-6 rounded-xl border">
        <div className="flex flex-col gap-2">
          <label className="text-sm font-medium">内容<span className="text-red-500">*</span></label>
          <textarea name="content" required rows={6} className="w-full resize-y rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" placeholder="いま何してる？" />
        </div>
        <div className="flex flex-col gap-2">
          <label className="text-sm font-medium">タグ (カンマ区切り)</label>
          <input name="tags" className="rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" placeholder="demo, nextjs" />
        </div>
        <div className="flex flex-col gap-2">
          <label className="text-sm font-medium">画像URL (改行区切り)</label>
          <textarea name="images" rows={3} className="w-full resize-y rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" placeholder="https://example.com/a.jpg\nhttps://example.com/b.png" />
        </div>
        <div className="flex items-center gap-3">
          <button type="submit" className="px-5 py-2 rounded-md bg-indigo-600 text-white text-sm font-medium hover:bg-indigo-700 transition-colors">
            投稿する
          </button>
          <a href="/home" className="text-sm text-neutral-500 hover:text-neutral-700">キャンセル</a>
        </div>
      </form>
      <p className="mt-4 text-xs text-neutral-500">※ ログインしていない場合はログインページへリダイレクトします。</p>
    </div>
  );
}
