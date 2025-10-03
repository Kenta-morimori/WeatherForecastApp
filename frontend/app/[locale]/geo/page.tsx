"use client";

import { ResultCard } from "@/components/result-card";
// 既存のコンポーネントをそのまま使う想定
import { SearchForm } from "@/components/search-form";
import { useTranslation } from "react-i18next";
// 地図は dynamic import で SSR 禁止のまま

export default function GeoPage() {
	const { t } = useTranslation("common");

	return (
		<div className="space-y-6">
			<h1 className="text-2xl md:text-3xl font-semibold tracking-tight">
				{t("title_geo")}
			</h1>

			{/* SearchForm が受け取らない props（placeholder/aria-label）は渡さない */}
			<div className="space-y-2">
				<label
					htmlFor="place-search"
					className="block text-sm font-medium text-zinc-700 dark:text-zinc-200"
				>
					{t("search_label")}
				</label>
				<SearchForm
					// 既存の props に合わせて適宜差し込む
					onSubmit={(payload) => {
						/* 既存ロジック */
					}}
					className="mt-1"
				/>
			</div>

			{/* 地図領域をセマンティックな <section> として宣言 */}
			<section
				aria-labelledby="map-heading"
				aria-describedby="map-help"
				className="rounded-xl overflow-hidden border border-zinc-200/60 dark:border-zinc-800/60"
			>
				<h2 id="map-heading" className="sr-only">
					{t("map_label")}
				</h2>
				{/* Map コンポーネント */}
			</section>

			<p id="map-help" className="text-sm text-zinc-500 dark:text-zinc-400">
				Tab/Shift+Tab で操作要素に移動できます。Enter で決定、Esc
				で候補を閉じます。
			</p>

			<ResultCard
			// 文言を t('...') に寄せる（内部も必要に応じて t 化）
			/>
		</div>
	);
}
