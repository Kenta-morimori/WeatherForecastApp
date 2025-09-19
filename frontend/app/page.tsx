'use client';
import { type ChartPoint, PredictionChart } from '@/components/prediction-chart';
import { ResultCard } from '@/components/result-card';
import { Button } from '@/components/ui/button';
import {
	Dialog,
	DialogContent,
	DialogFooter,
	DialogHeader,
	DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useToast } from '@/components/ui/use-toast';
import { usePredict } from '@/hooks/usePredict';
import type { PredictResponse, SeriesPoint } from '@/lib/api';
import QueryProvider from '@/providers/query-provider';
import { useState } from 'react';

export default function Page() {
	return (
		<QueryProvider>
			<MainPage />
		</QueryProvider>
	);
}

function MainPage() {
	const { toast } = useToast();
	const [lat, setLat] = useState<string>('35.6812'); // Tokyo Station
	const [lon, setLon] = useState<string>('139.7671');
	const [tz, setTz] = useState<string>('Asia/Tokyo');
	const [submitted, setSubmitted] = useState<{ lat: number; lon: number; tz: string } | null>(null);

	const { data, isLoading, isError, error } = usePredict(
		submitted ? { lat: submitted.lat, lon: submitted.lon, tz: submitted.tz } : null,
	);
	const [showError, setShowError] = useState(false);

	function onSubmit(e: React.FormEvent) {
		e.preventDefault();
		const latNum = Number(lat);
		const lonNum = Number(lon);
		if (Number.isNaN(latNum) || Number.isNaN(lonNum)) {
			toast({
				title: '入力エラー',
				description: '緯度・経度は数値で入力してください。',
				variant: 'destructive',
			});
			return;
		}
		setSubmitted({ lat: latNum, lon: lonNum, tz });
	}

	if (isError && !showError) {
		// Toast を即出し、Dialog は明示的に開く方式にしたい場合は setShowError(true) をここで呼ぶ
		toast({
			title: '取得に失敗しました',
			description: error?.message ?? '不明なエラー',
			variant: 'destructive',
		});
	}

	const chartData: ChartPoint[] = buildChartData(data);

	return (
		<div className="mx-auto max-w-4xl p-4 sm:p-6 space-y-6">
			<h1 className="text-2xl sm:text-3xl font-semibold">Weather Forecast</h1>

			<form onSubmit={onSubmit} className="grid grid-cols-1 sm:grid-cols-4 gap-3">
				<div>
					<Label htmlFor="lat">緯度 (lat)</Label>
					<Input
						id="lat"
						value={lat}
						onChange={(e) => setLat(e.target.value)}
						placeholder="35.6812"
					/>
				</div>
				<div>
					<Label htmlFor="lon">経度 (lon)</Label>
					<Input
						id="lon"
						value={lon}
						onChange={(e) => setLon(e.target.value)}
						placeholder="139.7671"
					/>
				</div>
				<div>
					<Label htmlFor="tz">タイムゾーン</Label>
					<Input
						id="tz"
						value={tz}
						onChange={(e) => setTz(e.target.value)}
						placeholder="Asia/Tokyo"
					/>
				</div>
				<div className="flex items-end">
					<Button type="submit" className="w-full">
						予測する
					</Button>
				</div>
			</form>

			{isLoading && (
				<div className="grid grid-cols-1 sm:grid-cols-2 gap-4 animate-pulse">
					<div className="h-32 bg-muted rounded-2xl" />
					<div className="h-32 bg-muted rounded-2xl" />
				</div>
			)}

			{/* Dialog は任意で開く */}
			<Dialog open={showError} onOpenChange={setShowError}>
				<DialogContent>
					<DialogHeader>
						<DialogTitle>エラー</DialogTitle>
					</DialogHeader>
					<p className="text-sm">{error?.message ?? '不明なエラーが発生しました。'}</p>
					<DialogFooter>
						<Button onClick={() => setShowError(false)}>閉じる</Button>
					</DialogFooter>
				</DialogContent>
			</Dialog>

			{data && (
				<div className="space-y-6">
					<div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
						<ResultCard title="きょう (D0)" data={data.d0} />
						<ResultCard title="あす (D1)" data={data.d1} />
					</div>
					{chartData.length > 0 && <PredictionChart data={chartData} />}
				</div>
			)}
		</div>
	);
}

function buildChartData(resp: PredictResponse | null | undefined): ChartPoint[] {
	if (!resp) return [];
	const f: SeriesPoint[] = resp.forecast_series ?? [];
	const a: SeriesPoint[] = resp.recent_actuals ?? [];

	const byDate = new Map<string, ChartPoint>();

	for (const p of a) {
		byDate.set(p.date, { date: p.date, actual: p.value ?? null, predicted: null });
	}
	for (const p of f) {
		const ex = byDate.get(p.date);
		if (ex) ex.predicted = p.value ?? null;
		else byDate.set(p.date, { date: p.date, predicted: p.value ?? null, actual: null });
	}
	return Array.from(byDate.values()).sort((x, y) => x.date.localeCompare(y.date));
}
