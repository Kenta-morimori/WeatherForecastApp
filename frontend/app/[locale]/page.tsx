// src/components/GeoPredict.tsx
'use client';

import 'leaflet/dist/leaflet.css';
import type { Icon } from 'leaflet';
import dynamic from 'next/dynamic';
import type React from 'react';
import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import type { MapContainerProps, MarkerProps, TileLayerProps } from 'react-leaflet';
import { useMapEvents } from 'react-leaflet';

const MapContainer = dynamic<MapContainerProps>(
	() => import('react-leaflet').then((m) => m.MapContainer),
	{ ssr: false },
);
const TileLayer = dynamic<TileLayerProps>(() => import('react-leaflet').then((m) => m.TileLayer), {
	ssr: false,
});
const Marker = dynamic<MarkerProps>(() => import('react-leaflet').then((m) => m.Marker), {
	ssr: false,
});

// API base
const API_BASE = (process.env.NEXT_PUBLIC_BACKEND_URL ?? 'http://127.0.0.1:8000').replace(
	/\/$/,
	'',
);

type GeocodeItem = { name?: string | null; display_name?: string | null; lat: number; lon: number };
type GeocodeSearchResponse = { q: string; source: 'live' | 'cache'; results: GeocodeItem[] };
type PredictPayload = {
	backend: string;
	date_d0: string;
	date_d1: string;
	prediction: { d1_mean: number; d1_min: number; d1_max: number; d1_prec: number };
};

function ClickPicker({ onPick }: { onPick: (lat: number, lon: number) => void }) {
	useMapEvents({
		click(e) {
			onPick(e.latlng.lat, e.latlng.lng);
		},
	});
	return null;
}

export default function GeoPredict() {
	const { t, i18n } = useTranslation('common');

	const [query, setQuery] = useState('');
	const routeLang = useMemo(
		() => (i18n.language?.startsWith('en') ? 'en' : 'ja') as 'ja' | 'en',
		[i18n.language],
	);
	const [lang, setLang] = useState<'ja' | 'en'>(routeLang);

	const [hits, setHits] = useState<GeocodeItem[]>([]);
	const [center, setCenter] = useState<[number, number]>([35.6812, 139.7671]);
	const [marker, setMarker] = useState<[number, number] | null>([35.6812, 139.7671]);
	const [loading, setLoading] = useState(false);
	const [pred, setPred] = useState<PredictPayload | null>(null);
	const [error, setError] = useState<string | null>(null);
	const [markerIcon, setMarkerIcon] = useState<Icon | null>(null);

	// ⬇ これを追加：クライアントにマウント完了するまで Map を描画しない
	const [isClient, setIsClient] = useState(false);
	useEffect(() => {
		setIsClient(true);
	}, []);

	useEffect(() => {
		(async () => {
			const L = await import('leaflet');
			const icon = L.icon({
				iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
				iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
				shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
				iconSize: [25, 41],
				iconAnchor: [12, 41],
				popupAnchor: [1, -34],
				shadowSize: [41, 41],
			});
			setMarkerIcon(icon);
		})();
	}, []);

	const toMessage = (e: unknown) =>
		e instanceof Error ? e.message : typeof e === 'string' ? e : 'unknown error';

	async function doGeocode(q: string) {
		setError(null);
		if (!q.trim()) {
			setHits([]);
			return;
		}
		try {
			const params = new URLSearchParams({ q, limit: String(5), lang, countrycodes: 'jp' });
			const res = await fetch(`${API_BASE}/api/geocode/search?${params.toString()}`);
			if (!res.ok) throw new Error(await res.text());
			const data = (await res.json()) as GeocodeSearchResponse;
			const results = Array.isArray(data.results)
				? data.results.filter(
						(r): r is GeocodeItem => typeof r?.lat === 'number' && typeof r?.lon === 'number',
					)
				: [];
			setHits(results);
		} catch (e) {
			setError(`${t('error_fetch')}: ${toMessage(e)}`);
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
			setError(`${t('error_fetch')}: ${toMessage(e)}`);
		} finally {
			setLoading(false);
		}
	}

	function handlePick(lat: number, lon: number) {
		setMarker([lat, lon]);
		setCenter([lat, lon]);
		void doPredict(lat, lon);
	}

	const inputId = 'geocode-input';
	const langId = 'lang-select';
	const selectId = 'geocode-results';

	return (
		<div className="w-full max-w-4xl mx-auto grid gap-4 p-4">
			<h2 className="text-xl md:text-2xl font-semibold tracking-tight">{t('title_geo')}</h2>

			<div className="flex gap-2 items-end">
				<div className="flex-1">
					<label
						htmlFor={inputId}
						className="block text-sm font-medium text-zinc-700 dark:text-zinc-200"
					>
						{t('search_label')}
					</label>
					<input
						id={inputId}
						className="mt-1 w-full border rounded-lg px-3 py-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500"
						placeholder={t('placeholder_search')}
						value={query}
						onChange={(e: React.ChangeEvent<HTMLInputElement>) => setQuery(e.target.value)}
						onKeyDown={(e: React.KeyboardEvent<HTMLInputElement>) => {
							if (e.key === 'Enter') void doGeocode(query);
						}}
					/>
				</div>

				<div>
					<label
						htmlFor={langId}
						className="block text-sm font-medium text-zinc-700 dark:text-zinc-200"
					>
						{t('label_language')}
					</label>
					<select
						id={langId}
						className="mt-1 border rounded-lg px-2 py-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500"
						value={lang}
						onChange={(e: React.ChangeEvent<HTMLSelectElement>) =>
							setLang(e.target.value as 'ja' | 'en')
						}
						title={t('label_language')}
						aria-label={t('label_language')}
					>
						<option value="ja">日本語</option>
						<option value="en">English</option>
					</select>
				</div>

				<button
					type="button"
					className="inline-flex items-center rounded-lg px-4 py-2 bg-indigo-600 text-white hover:bg-indigo-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2"
					onClick={() => void doGeocode(query)}
				>
					{t('btn_search')}
				</button>
			</div>

			{hits.length > 0 && (
				<div className="border rounded-xl p-3">
					<label
						htmlFor={selectId}
						className="block text-sm font-medium text-zinc-700 dark:text-zinc-200 mb-1"
					>
						{t('search_label')}
					</label>
					<select
						id={selectId}
						size={Math.min(hits.length, 5)}
						className="w-full border rounded-lg px-2 py-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500"
						onChange={(e: React.ChangeEvent<HTMLSelectElement>) => {
							const idx = e.target.selectedIndex;
							const item = hits[idx];
							if (item) handlePick(item.lat, item.lon);
						}}
						aria-describedby="geocode-hint"
					>
						{hits.map((h) => {
							const label = (h.name ?? h.display_name ?? '').trim();
							const coords = `${h.lat.toFixed(5)}, ${h.lon.toFixed(5)}`;
							return (
								<option
									key={`${h.lat}-${h.lon}`}
									value={coords}
									title={label ? `${label} (${coords})` : coords}
								>
									{label ? `${label} — ${coords}` : coords}
								</option>
							);
						})}
					</select>
					<p id="geocode-hint" className="mt-1 text-xs text-zinc-500">
						Enter で選択、Tab で移動できます。
					</p>
				</div>
			)}

			{/* ⬇ マウント完了＆アイコン準備ができたら描画 */}
			<section
				aria-labelledby="map-heading"
				aria-describedby="map-help"
				className="rounded-2xl overflow-hidden border border-zinc-200/60 dark:border-zinc-800/60 shadow-[0_1px_24px_-8px_rgba(0,0,0,0.25)]"
			>
				<h3 id="map-heading" className="sr-only">
					{t('map_label')}
				</h3>
				<div className="h-[420px] w-full">
					{isClient && markerIcon ? (
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
							{marker && <Marker position={marker} icon={markerIcon} />}
						</MapContainer>
					) : null}
				</div>
			</section>

			<p id="map-help" className="text-sm text-zinc-500 dark:text-zinc-400">
				{t('hint_start')}
			</p>

			<div className="grid gap-2" aria-live="polite">
				{loading && <div className="text-sm">{t('loading_predict')}</div>}
				{error && <div className="text-sm text-red-600">{error}</div>}
				{pred ? (
					<div className="rounded-2xl border border-zinc-200/60 dark:border-zinc-800/60 p-4 bg-white/70 dark:bg-zinc-900/50">
						<div className="text-sm text-zinc-500 mb-1">
							backend: {pred.backend} / {t('today')}: {pred.date_d0} / {t('tomorrow')}:{' '}
							{pred.date_d1}
						</div>
						<div className="text-lg">
							{t('pred_tomorrow', {
								mean: pred.prediction.d1_mean.toFixed(1),
								min: pred.prediction.d1_min.toFixed(1),
								max: pred.prediction.d1_max.toFixed(1),
								prec: pred.prediction.d1_prec.toFixed(1),
							})}
						</div>
					</div>
				) : (
					!loading && <div className="text-sm text-zinc-500">{t('hint_start')}</div>
				)}
			</div>

			<div className="text-xs text-zinc-500 mt-2">{t('osm_attribution')}</div>
		</div>
	);
}
