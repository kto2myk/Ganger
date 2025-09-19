import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';

export default function SettingsPage() {
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
          <h1 className="text-2xl font-bold text-gray-900">設定</h1>
        </div>

        {/* メインコンテンツ */}
        <div className="space-y-6">
          {/* アカウント設定 */}
          <div className="bg-white rounded-xl shadow-sm border p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">アカウント設定</h2>
            <p className="text-gray-600 text-center">
              アカウント設定機能は現在開発中です。
            </p>
            
            {/* 予定されている機能のプレビュー */}
            <div className="mt-4">
              <h4 className="font-medium text-gray-900 mb-2">実装予定の機能</h4>
              <ul className="space-y-1 text-gray-600 text-sm">
                <li>• パスワード変更</li>
                <li>• メールアドレス変更</li>
                <li>• アカウント削除</li>
              </ul>
            </div>
          </div>

          {/* プライバシー設定 */}
          <div className="bg-white rounded-xl shadow-sm border p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">プライバシー設定</h2>
            <p className="text-gray-600 text-center">
              プライバシー設定機能は現在開発中です。
            </p>
            
            <div className="mt-4">
              <h4 className="font-medium text-gray-900 mb-2">実装予定の機能</h4>
              <ul className="space-y-1 text-gray-600 text-sm">
                <li>• 投稿の公開設定</li>
                <li>• フォロー承認制</li>
                <li>• ブロック機能</li>
              </ul>
            </div>
          </div>

          {/* 通知設定 */}
          <div className="bg-white rounded-xl shadow-sm border p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">通知設定</h2>
            <p className="text-gray-600 text-center">
              通知設定機能は現在開発中です。
            </p>
            
            <div className="mt-4">
              <h4 className="font-medium text-gray-900 mb-2">実装予定の機能</h4>
              <ul className="space-y-1 text-gray-600 text-sm">
                <li>• いいね通知</li>
                <li>• コメント通知</li>
                <li>• フォロー通知</li>
                <li>• メッセージ通知</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}