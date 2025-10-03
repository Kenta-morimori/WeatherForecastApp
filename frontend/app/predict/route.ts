import { type NextRequest, NextResponse } from "next/server";

function clamp(n: number, min: number, max: number) {
	return Math.max(min, Math.min(max, n));
}

export async function GET(req: NextRequest) {
	const { searchParams } = new URL(req.url);
	const lat = Number(searchParams.get("lat") ?? "0");
	const lon = Number(searchParams.get("lon") ?? "0");
	const tz = searchParams.get("tz") ?? "Asia/Tokyo";

	const seed = Math.abs(Math.sin(lat * 12.9898 + lon * 78.233));
	const rnd = (a: number, b: number) => a + (b - a) * (seed % 1);

	const max0 = clamp(Number(rnd(27, 33).toFixed(1)), -50, 60);
	const min0 = clamp(Number((max0 - rnd(5, 9)).toFixed(1)), -60, max0);
	const prp0 = Number(rnd(0.2, 0.8).toFixed(2));
	const pmm0 = Number(rnd(0, 10).toFixed(1));

	const drift = rnd(-1.5, 1.5);
	const max1 = clamp(Number((max0 + drift).toFixed(1)), -50, 60);
	const min1 = clamp(Number((min0 + drift).toFixed(1)), -60, max1);
	const prp1 = Number(clamp(prp0 + rnd(-0.15, 0.15), 0, 1).toFixed(2));
	const pmm1 = Number(clamp(pmm0 + rnd(-3, 3), 0, 20).toFixed(1));

	return NextResponse.json({
		d0: { max: max0, min: min0, precip_prob: prp0, precip: pmm0 },
		d1: { max: max1, min: min1, precip_prob: prp1, precip: pmm1 },
		forecast_series: [],
		recent_actuals: [],
		_meta: { lat, lon, tz, mock: true },
	});
}
