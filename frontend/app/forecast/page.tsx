'use client';

import { ResultCard } from '@/components/result-card';
import { SearchForm, type SearchFormPayload } from '@/components/search-form';
import { useToast } from '@/components/ui/use-toast';
import { usePredict } from '@/hooks/usePredict';
import { useEffect, useState } from 'react';

export default function Page() {
	const { toast } = useToast();
	const [query, setQuery] = useState<{ lat: number; lon: number } | null>(null);

	const { data, error, loading } = usePredict(query ? { ...query, tz: 'Asia/Tokyo' } : null);

	// ✅ エラーが変化した時だけトースト
	useEffect(() => {
		if (!error) return;
		toast({
			title: '取得に失敗しました',
			description: error,
			variant: 'destructive',
		});
	}, [error, toast]);

	return (
		<main className="space-y-6 p-4">
			<SearchForm
				onSubmit={(payload: SearchFormPayload) => {
					const { lat, lon } = payload;
					if (lat === '' || lon === '') {
						toast({
							title: '未対応',
							description: '現在は緯度・経度の直接入力のみ対応しています。',
						});
						return;
					}
					setQuery({ lat: Number(lat), lon: Number(lon) });
				}}
			/>

			{loading && <div className="text-sm text-gray-500">予測を取得中…</div>}

			{data && (
				<div className="grid gap-4 md:grid-cols-2">
					<ResultCard title="D0（今日）" data={data.d0} />
					<ResultCard title="D1（明日）" data={data.d1} />
				</div>
			)}
		</main>
	);
}
