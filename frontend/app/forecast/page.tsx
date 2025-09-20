// app/forecast/page.tsx
'use client';

import { ResultCard } from '@/components/result-card';
import { SearchForm } from '@/components/search-form';
import { type PredictResponse, fetchPredict } from '@/lib/api';
import { useState } from 'react';

type ViewState = {
	label: string;
	res: PredictResponse;
} | null;

export default function Page() {
	const [view, setView] = useState<ViewState>(null);
	const [loading, setLoading] = useState(false);
	const [error, setError] = useState<string | null>(null);

	return (
		<main className="space-y-6">
			<SearchForm
				onSubmit={async (payload) => {
					// 緯度経度がない場合は今は未対応（将来はジオコーディングで対応）。
					if (payload.lat === '' || payload.lon === '') {
						setError('いまは緯度・経度の入力が必要です。');
						return;
					}

					const ctrl = new AbortController();
					setLoading(true);
					setError(null);
					setView(null);

					const trimmedName = (payload.name ?? '').trim();
					const label =
						trimmedName.length > 0
							? trimmedName
							: `${Number(payload.lat).toFixed(3)}, ${Number(payload.lon).toFixed(3)}`;

					try {
						const tz = Intl.DateTimeFormat().resolvedOptions().timeZone ?? 'Asia/Tokyo';
						const res = await fetchPredict(
							{ lat: Number(payload.lat), lon: Number(payload.lon), tz },
							ctrl.signal,
						);
						setView({ label, res });
					} catch (e) {
						console.error(e);
						setError('取得に失敗しました。時間をおいて再度お試しください。');
					} finally {
						setLoading(false);
					}

					// 画面遷移や再検索時のキャンセル用に返しておくと安全
					return () => ctrl.abort();
				}}
			/>

			{loading && <p className="text-sm text-gray-600">予測を取得中...</p>}
			{error && <p className="text-sm text-red-600">{error}</p>}

			{view && (
				<section className="space-y-3">
					<div className="text-sm text-gray-500">{view.label}</div>
					<div className="grid gap-4 md:grid-cols-2">
						<ResultCard title="今日 (D0)" data={view.res.d0} />
						<ResultCard title="明日 (D1)" data={view.res.d1} />
					</div>
				</section>
			)}
		</main>
	);
}
