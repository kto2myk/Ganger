import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';

export default function EditProfilePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50">
      <div className="max-w-2xl mx-auto px-4 py-8">
        {/* ヘッダー */}
        <div className="mb-6">
          <Link 
            href="/home"
            className="inline-flex items-center text-gray-600 hover:text-gray-900 transition-colors mb-4 no-underline hover:no-underline"
          >
            <ArrowLeft className="w-5 h-5 mr-2" />
            戻る
          </Link>
          <h1 className="text-2xl font-bold text-gray-900">プロフィール編集</h1>
        </div>

        {/* メインコンテンツ */}
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <p className="text-gray-600 text-center">
            プロフィール編集機能は現在開発中です。
          </p>
          <p className="text-gray-500 text-center text-sm mt-2">
            近日中に実装予定です。
          </p>
          
          {/* 予定されている機能のプレビュー */}
          <div className="mt-8">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">実装予定の機能</h3>
            <ul className="space-y-2 text-gray-600">
              <li>• プロフィール画像の変更</li>
              <li>• 表示名の編集</li>
              <li>• バイオの編集</li>
              <li>• 住所の編集</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}