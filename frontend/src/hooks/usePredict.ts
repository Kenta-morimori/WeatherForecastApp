'use client';
import { type PredictInput, type PredictResponse, fetchPredict } from '@/lib/api';
import { useEffect, useState } from 'react';

export function usePredict(params: PredictInput | null) {
	const [data, setData] = useState<PredictResponse | null>(null);
	const [error, setError] = useState<string | null>(null);
	const [loading, setLoading] = useState(false);

	useEffect(() => {
		if (!params) {
			setData(null);
			setError(null);
			setLoading(false);
			return;
		}
		const ctrl = new AbortController();

		(async () => {
			try {
				setLoading(true);
				setError(null);
				const res = await fetchPredict(params, ctrl.signal);
				setData(res);
			} catch (e) {
				setError(e instanceof Error ? e.message : String(e));
			} finally {
				setLoading(false);
			}
		})();

		return () => ctrl.abort();
	}, [params]); // ✅ Biome が満足する形

	return { data, error, loading };
}
