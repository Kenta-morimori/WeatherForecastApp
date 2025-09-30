// app/[locale]/page.tsx（例：ヒーローのボタンをリンクに）
'use client';
import { usePathname, useRouter } from 'next/navigation';

export default function LocaleIndexPage() {
	const router = useRouter();
	const pathname = usePathname(); // /ja or /en
	const locale = pathname?.split('/')[1] === 'en' ? 'en' : 'ja';

	return (
		<div className="mx-auto max-w-3xl px-6 py-10">
			<div className="rounded-2xl bg-zinc-900/50 text-white p-10 shadow-2xl backdrop-blur">
				<h1 className="text-4xl font-bold mb-4">場所を検索して予測</h1>
				<p className="text-zinc-300 mb-6">
					地図をクリック、または検索結果を選ぶと予測を表示します。
				</p>
				<div className="flex gap-3">
					<button
						type="button"
						onClick={() => router.push(`/${locale}/geo`)}
						className="rounded-lg px-5 py-2 bg-indigo-600 hover:bg-indigo-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400"
					>
						検索
					</button>
					<button
						type="button"
						onClick={() => router.push(`/${locale}/forecast`)}
						className="rounded-lg px-5 py-2 bg-zinc-200 text-zinc-900 hover:bg-zinc-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400"
					>
						Forecast
					</button>
				</div>
			</div>
		</div>
	);
}
