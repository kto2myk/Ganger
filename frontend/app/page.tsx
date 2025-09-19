import { redirect } from 'next/navigation';

// ルートページをホームページにリダイレクト
export default function RootPage() {
  redirect('/home');
}
