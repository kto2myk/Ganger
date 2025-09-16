import React from 'react';
import Image from 'next/image';

interface PostCardProps {
  post: any;
}

export function PostCard({ post }: PostCardProps) {
  return (
    <article className="rounded-xl border bg-white/70 backdrop-blur-sm shadow-sm p-4 flex flex-col gap-3 hover:shadow-md transition-shadow">
      <header className="flex items-start gap-3">
        <div className="size-10 rounded-full bg-gradient-to-br from-indigo-400 to-indigo-600 text-white flex items-center justify-center text-sm font-semibold">
          {post.author?.username?.[0]?.toUpperCase() || 'U'}
        </div>
        <div className="flex flex-col text-sm">
          <span className="font-medium text-neutral-800">{post.author?.username || 'Unknown User'}</span>
          <span className="text-neutral-500 text-xs">{new Date(post.createdAt || Date.now()).toLocaleString()}</span>
        </div>
      </header>
      <div className="text-sm leading-relaxed whitespace-pre-wrap break-words">
        {post.content}
      </div>
      {post.images && post.images.length > 0 && (
        <div className="grid gap-2" style={{ gridTemplateColumns: `repeat(${Math.min(post.images.length, 3)}, 1fr)` }}>
          {post.images.slice(0, 6).map((img: any) => (
            <div key={img.id} className="relative aspect-[4/3] overflow-hidden rounded-lg bg-neutral-200">
              <Image src={img.url} alt="post image" fill className="object-cover" />
            </div>
          ))}
        </div>
      )}
      <footer className="flex items-center gap-4 pt-1 text-xs text-neutral-600">
        <button className="hover:text-indigo-600 transition-colors">Like {post.likes?.length ? `(${post.likes.length})` : ''}</button>
        <button className="hover:text-indigo-600 transition-colors">Repost</button>
        <button className="hover:text-indigo-600 transition-colors">Save</button>
      </footer>
    </article>
  );
}
