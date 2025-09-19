'use client';

import React, { useState, useRef, useCallback } from 'react';
import Image from 'next/image';
import { useSession } from 'next-auth/react';
import { uploadImage } from '@/actions/upload';
import { createPost } from '@/actions/posts';

interface InlinePostCreatorProps {
  onPostCreated?: () => void;
}

export function InlinePostCreator({ onPostCreated }: InlinePostCreatorProps) {
  const { data: session } = useSession();
  const [content, setContent] = useState('');
  const [images, setImages] = useState<string[]>([]);
  const [uploading, setUploading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const files = Array.from(e.dataTransfer.files);
    const imageFiles = files.filter(file => file.type.startsWith('image/'));
    
    if (imageFiles.length > 0) {
      await uploadFiles(imageFiles);
    }
  }, []);

  const uploadFiles = async (files: File[]) => {
    setUploading(true);
    const newImages: string[] = [];
    
    for (const file of files) {
      try {
        const formData = new FormData();
        formData.append('file', file);
        const result = await uploadImage(formData);
        
        if (result.success && result.url) {
          newImages.push(result.url);
        } else {
          console.error('Upload failed:', result.error);
        }
      } catch (error) {
        console.error('Upload error:', error);
      }
    }
    
    setImages(prev => [...prev, ...newImages]);
    setUploading(false);
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length > 0) {
      await uploadFiles(files);
    }
  };

  const removeImage = (index: number) => {
    setImages(prev => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!content.trim() && images.length === 0) return;

    setSubmitting(true);
    try {
      const formData = new FormData();
      formData.append('content', content);
      images.forEach(url => formData.append('images', url));

      const result = await createPost(formData);
      if (result.success) {
        setContent('');
        setImages([]);
        setExpanded(false);
        onPostCreated?.();
      }
    } catch (error) {
      console.error('Post creation failed:', error);
    } finally {
      setSubmitting(false);
    }
  };

  if (!session) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-4 mb-6">
        <p className="text-gray-500 text-center">投稿するにはログインが必要です</p>
      </div>
    );
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 mb-6">
      <form onSubmit={handleSubmit}>
        <div
          className={`relative ${dragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-200'} border-2 border-dashed rounded-lg p-3 transition-colors`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            onFocus={() => setExpanded(true)}
            placeholder={dragActive ? "ファイルをドロップしてください" : "今何してる？"}
            className="w-full resize-none border-none outline-none text-gray-900 placeholder-gray-500"
            rows={expanded ? 4 : 2}
          />
          
          {dragActive && (
            <div className="absolute inset-0 flex items-center justify-center bg-blue-50 bg-opacity-90 border-2 border-dashed border-blue-500 rounded-lg">
              <div className="text-blue-600 text-center">
                <svg className="mx-auto w-12 h-12 mb-2" fill="none" stroke="currentColor" viewBox="0 0 48 48">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" />
                </svg>
                <p className="text-sm font-medium">画像をドロップ</p>
              </div>
            </div>
          )}
        </div>

        {/* 画像プレビュー */}
        {images.length > 0 && (
          <div className="mt-3 grid grid-cols-2 gap-2">
            {images.map((url, index) => (
              <div key={index} className="relative">
                <Image
                  src={url}
                  alt={`アップロード画像 ${index + 1}`}
                  width={200}
                  height={128}
                  className="w-full h-32 object-cover rounded-lg"
                />
                <button
                  type="button"
                  onClick={() => removeImage(index)}
                  className="absolute top-2 right-2 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm hover:bg-red-600"
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        )}

        {(expanded || content.trim() || images.length > 0) && (
          <div className="flex items-center justify-between mt-3 pt-3 border-t border-gray-100">
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                disabled={uploading}
                className="flex items-center gap-1 px-3 py-1.5 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-md transition-colors disabled:opacity-50"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                {uploading ? '読み込み中...' : '画像'}
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                multiple
                onChange={handleFileSelect}
                className="hidden"
              />
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => {
                  setContent('');
                  setImages([]);
                  setExpanded(false);
                }}
                className="px-4 py-1.5 text-sm text-gray-600 hover:text-gray-800 transition-colors"
              >
                キャンセル
              </button>
              <button
                type="submit"
                disabled={submitting || uploading || (!content.trim() && images.length === 0)}
                className="px-4 py-1.5 text-sm bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {submitting ? '投稿中...' : '投稿'}
              </button>
            </div>
          </div>
        )}
      </form>
    </div>
  );
}