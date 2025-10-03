export type PredictInput = { lat: number; lon: number; tz?: string };
export type DayBlock = {
	max?: number | null;
	min?: number | null;
	precip_prob?: number | null; // 0-1 or 0-100
	precip?: number | null; // mm
};
export type SeriesPoint = { date: string; value: number | null };
export type PredictResponse = {
	d0?: DayBlock;
	d1?: DayBlock;
	forecast_series?: SeriesPoint[];
	recent_actuals?: SeriesPoint[];
};

const BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "";

export async function fetchPredict(
	params: PredictInput,
	signal?: AbortSignal,
): Promise<PredictResponse> {
	const tz = params.tz ?? "Asia/Tokyo";
	const qs = new URLSearchParams({
		lat: String(params.lat),
		lon: String(params.lon),
		tz,
	});
	const res = await fetch(`${BASE_URL}/predict?${qs.toString()}`, { signal });
	if (!res.ok) {
		const text = await res.text().catch(() => "");
		throw new Error(text || `Request failed: ${res.status}`);
	}
	return (await res.json()) as PredictResponse;
}
