"use client";
import {
	type PredictInput,
	type PredictResponse,
	fetchPredict,
} from "@/lib/api";
import { useEffect, useState } from "react";

export function usePredict(params: PredictInput | null) {
	const [data, setData] = useState<PredictResponse | null>(null);
	const [error, setError] = useState<string | null>(null);
	const [loading, setLoading] = useState(false);

	useEffect(() => {
		if (!params) return;
		const ctrl = new AbortController();
		setLoading(true);
		setError(null);
		fetchPredict(params, ctrl.signal)
			.then(setData)
			.catch((e) => setError(e instanceof Error ? e.message : String(e)))
			.finally(() => setLoading(false));
		return () => ctrl.abort();
	}, [params]); // ← 依存は params のみ

	return { data, error, loading };
}
