'use client';

import L from 'leaflet';
import dynamic from 'next/dynamic';
import React, { useState } from 'react';
import type { MapContainerProps } from 'react-leaflet';
import { Marker as MarkerBase, useMapEvents } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

// Leaflet のアイコンは Marker に直接渡す（prototype 書き換え回避）
const DefaultIcon = L.icon({
	iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
	iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
	shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
	iconSize: [25, 41],
	iconAnchor: [12, 41],
});

// SSR を切ったコンポーネント（Map/Tile/Marker）
const MapContainer = dynamic(() => import('react-leaflet').then((m) => m.MapContainer), {
	ssr: false,
});
const TileLayer = dynamic(() => import('react-leaflet').then((m) => m.TileLayer), { ssr: false });
const Marker = dynamic(() => import('react-leaflet').then((m) => m.Marker), { ssr: false });

// API base
const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? '';

type GeocodeItem = {
	name?: string | null;
	display_name?: string | null;
	lat: number;
	lon: number;
};

type GeocodeSearchResponse = {
	q: string;
	source: 'live' | 'cache';
	results: GeocodeItem[];
};

type PredictPayload = {
	backend: string;
	date_d0: string;
	date_d1: string;
	prediction: {
		d1_mean: number;
		d1_min: number;
		d1_max: number;
		d1_prec: number;
	};
};

function ClickPicker({ onPick }: { onPick: (lat: number, lon: number) => void }) {
	useMapEvents({
		click(e) {
			onPick(e.latlng.lat, e.latlng.lng);
		},
	});
	return null;
}

export default function GeoPredictClient() {
	const [query, setQuery] = useState('');
	const [lang, setLang] = useState('ja');
	const [hits, setHits] = useState<GeocodeItem[]>([]);
	const [center, setCenter] = useState<[number, number]>([35.6812, 139.7671]); // 東京駅
	const [marker, setMarker] = useState<[number, number] | null>([35.6812, 139.7671]);
	const [loading, setLoading] = useState(false);
	const [pred, setPred] = useState<PredictPayload | null>(null);
	const [error, setError] = useState<string | null>(null);

	const toMessage = (e: unknown) =>
		e instanceof Error ? e.message : typeof e === 'string' ? e : 'unknown error';

	async function doGeocode(q: string) {
		setError(null);
		if (!q.trim()) {
			setHits([]);
			return;
		}
		try {
			const url = `${API_BASE}/api/geocode/search?q=${encodeURIComponent(q)}&limit=5&lang=${lang}&countrycodes=jp`;
			const res = await fetch(url);
			if (!res.ok) throw new Error(await res.text());
			const data = (await res.json()) as GeocodeSearchResponse;
			const results = Array.isArray(data.results)
				? data.results.filter(
						(r): r is GeocodeItem => typeof r.lat === 'number' && typeof r.lon === 'number',
					)
				: [];
			setHits(results);
		} catch (e) {
			setError(`Geocode error: ${toMessage(e)}`);
			setHits([]);
		}
	}

	async function doPredict(lat: number, lon: number) {
		setLoading(true);
		setError(null);
		setPred(null);
		try {
			const res = await fetch(`${API_BASE}/predict`, {
				method: 'POST',
				headers: { 'content-type': 'application/json' },
				body: JSON.stringify({ lat, lon, tz: 'Asia/Tokyo' }),
			});
			if (!res.ok) throw new Error(await res.text());
			const data = (await res.json()) as PredictPayload;
			setPred(data);
		} catch (e) {
			setError(`Predict error: ${toMessage(e)}`);
		} finally {
			setLoading(false);
		}
	}

	function handlePick(lat: number, lon: number) {
		setMarker([lat, lon]);
		setCenter([lat, lon]);
		void doPredict(lat, lon);
	}

	return (
		<div className="w-full max-w-4xl mx-auto grid gap-4 p-4">
			<h2 className="text-xl font-semibold">場所を検索して予測</h2>

			<div className="flex gap-2 items-center">
				<input
					className="flex-1 border rounded px-3 py-2"
					placeholder="地名 / 駅名 / 住所（例: 東京駅）"
					value={query}
					onChange={(e) => setQuery(e.target.value)}
					onKeyDown={(e) => {
						if (e.key === 'Enter') void doGeocode(query);
					}}
				/>
				<select
					className="border rounded px-2 py-2"
					value={lang}
					onChange={(e) => setLang(e.target.value)}
					title="言語"
				>
					<option value="ja">日本語</option>
					<option value="en">English</option>
				</select>
				<button
					type="button"
					className="border rounded px-3 py-2 hover:bg-gray-50"
					onClick={() => void doGeocode(query)}
				>
					検索
				</button>
			</div>

			{hits.length > 0 && (
				<div className="border rounded p-2 max-h-48 overflow-auto">
					{hits.map((h) => {
						const key = `${h.lat.toFixed(5)},${h.lon.toFixed(5)}`;
						return (
							<button
								type="button"
								key={key}
								className="block text-left w-full px-2 py-1 hover:bg-gray-50"
								onClick={() => handlePick(h.lat, h.lon)}
								title={h.display_name ?? h.name ?? ''}
							>
								<div className="text-sm font-medium">{h.name ?? h.display_name}</div>
								<div className="text-xs text-gray-500">
									{h.lat.toFixed(5)}, {h.lon.toFixed(5)}
								</div>
							</button>
						);
					})}
				</div>
			)}

			<div className="h-[420px] w-full rounded overflow-hidden border">
				<MapContainer
					center={center}
					zoom={11}
					scrollWheelZoom
					style={{ height: '100%', width: '100%' } as MapContainerProps['style']}
				>
					<TileLayer
						attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
						url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
					/>
					<ClickPicker onPick={handlePick} />
					{marker && <Marker position={marker} icon={DefaultIcon} />}
				</MapContainer>
			</div>

			<div className="grid gap-2">
				{loading && <div className="text-sm">予測取得中…</div>}
				{error && <div className="text-sm text-red-600">{error}</div>}
				{pred && (
					<div className="border rounded p-3">
						<div className="text-sm text-gray-500 mb-1">
							backend: {pred.backend} / D0: {pred.date_d0} / D1: {pred.date_d1}
						</div>
						<div className="text-lg">
							明日の予測: 平均 {pred.prediction.d1_mean.toFixed(1)}℃（最低{' '}
							{pred.prediction.d1_min.toFixed(1)}℃ / 最高 {pred.prediction.d1_max.toFixed(1)}
							℃）・降水 {pred.prediction.d1_prec.toFixed(1)}mm
						</div>
					</div>
				)}
				{!pred && !loading && (
					<div className="text-sm text-gray-500">
						地図をクリック、または検索結果を選ぶと予測を表示します。
					</div>
				)}
			</div>

			<div className="text-xs text-gray-500 mt-2">
				地図タイル: © OpenStreetMap contributors（利用規約とレートを遵守）
			</div>
		</div>
	);
}
