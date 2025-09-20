'use client';

import { ResultCard } from '@/components/result-card';
import { SearchForm, type SearchFormPayload } from '@/components/search-form';
import { useToast } from '@/components/ui/use-toast';
import { usePredict } from '@/hooks/usePredict';
import { useEffect, useState } from 'react';

export default function Page() {
	const [params, setParams] = useState<{ lat: number; lon: number; tz?: string } | null>(null);
	const { data, error, loading } = usePredict(params);
	const { toast } = useToast();

	useEffect(() => {
		if (error) {
			toast({ title: '取得に失敗しました', description: error, variant: 'destructive' });
		}
	}, [error, toast]);

	return (
		<main className="space-y-6">
			<SearchForm
				onSubmit={(payload: SearchFormPayload) => {
					setParams({
						lat: Number(payload.lat),
						lon: Number(payload.lon),
						tz: 'Asia/Tokyo',
					});
				}}
			/>
			{loading && <p>Loading...</p>}
			{data && (
				<div className="grid gap-4 md:grid-cols-2">
					<ResultCard title="今日 (D0)" data={data.d0} />
					<ResultCard title="明日 (D1)" data={data.d1} />
				</div>
			)}
		</main>
	);
}
