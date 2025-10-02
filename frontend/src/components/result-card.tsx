'use client';
import React from 'react';
import { useTranslation } from 'react-i18next';

export type DayBlock = {
	max?: number | null;
	min?: number | null;
	precip_prob?: number | null; // 0-1 or 0-100
	precip?: number | null; // mm
};

type DCardProps = {
	title?: string;
	data?: DayBlock;
};

type MockCardProps = {
	locationLabel: string;
	tempMean: number;
	tempMin: number;
	tempMax: number;
	precipMm: number;
};

type Props = DCardProps | MockCardProps;

function fmt(n: number | null | undefined, digits = 1) {
	if (n === null || n === undefined || Number.isNaN(n)) return '-';
	return n.toFixed(digits);
}
function toPct(x: number | null | undefined) {
	if (x === null || x === undefined || Number.isNaN(x)) return '-';
	return x > 1 ? `${Math.round(x)}%` : `${Math.round(x * 100)}%`;
}

export function ResultCard(props: Props) {
	const { t } = useTranslation('common');

	// ---- モック版（locationLabel 付き） ----
	if ('locationLabel' in props) {
		const { locationLabel, tempMean, tempMin, tempMax, precipMm } = props;
		return (
			<section
				aria-label={t('title_geo') ?? 'Forecast'}
				className="w-full rounded-2xl border p-4 shadow bg-white/70 dark:bg-zinc-900/50"
			>
				{/* アクセシブルネーム補強（スクリーンリーダー向け見出し） */}
				<h3 className="sr-only">{t('title_geo') ?? 'Forecast'}</h3>

				<p className="mb-2 text-sm text-zinc-500">{locationLabel}</p>

				<dl className="grid grid-cols-2 gap-4 text-sm sm:text-base">
					<div className="rounded-2xl bg-zinc-100 p-3 dark:bg-zinc-800/60">
						<dt className="opacity-70">{t('label_max') ?? '最高'}</dt>
						<dd className="text-2xl font-semibold">{fmt(tempMax)}℃</dd>
					</div>
					<div className="rounded-2xl bg-zinc-100 p-3 dark:bg-zinc-800/60">
						<dt className="opacity-70">{t('label_min') ?? '最低'}</dt>
						<dd className="text-2xl font-semibold">{fmt(tempMin)}℃</dd>
					</div>
					<div className="rounded-2xl bg-zinc-100 p-3 dark:bg-zinc-800/60">
						<dt className="opacity-70">{t('label_mean') ?? '平均'}</dt>
						<dd className="text-2xl font-semibold">{fmt(tempMean)}℃</dd>
					</div>
					<div className="rounded-2xl bg-zinc-100 p-3 dark:bg-zinc-800/60">
						<dt className="opacity-70">{t('label_precip') ?? '降水量'}</dt>
						<dd className="text-2xl font-semibold">{fmt(precipMm, 1)} mm</dd>
					</div>
				</dl>
			</section>
		);
	}

	// ---- 通常版（DayBlock） ----
	const { title = '', data } = props;
	return (
		<section
			aria-label={title || (t('title_geo') ?? 'Forecast')}
			className="w-full rounded-2xl border p-4 shadow bg-white/70 dark:bg-zinc-900/50"
		>
			{title ? (
				<h3 className="mb-2 text-xl">{title}</h3>
			) : (
				<h3 className="sr-only">{t('title_geo') ?? 'Forecast'}</h3>
			)}

			<dl className="grid grid-cols-2 gap-4 text-sm sm:text-base">
				<div className="rounded-2xl bg-zinc-100 p-3 dark:bg-zinc-800/60">
					<dt className="opacity-70">{t('label_max') ?? '最高'}</dt>
					<dd className="text-2xl font-semibold">{fmt(data?.max)}℃</dd>
				</div>
				<div className="rounded-2xl bg-zinc-100 p-3 dark:bg-zinc-800/60">
					<dt className="opacity-70">{t('label_min') ?? '最低'}</dt>
					<dd className="text-2xl font-semibold">{fmt(data?.min)}℃</dd>
				</div>
				<div className="rounded-2xl bg-zinc-100 p-3 dark:bg-zinc-800/60">
					<dt className="opacity-70">{t('label_precip_prob') ?? '降水確率'}</dt>
					<dd className="text-2xl font-semibold">{toPct(data?.precip_prob)}</dd>
				</div>
				<div className="rounded-2xl bg-zinc-100 p-3 dark:bg-zinc-800/60">
					<dt className="opacity-70">{t('label_precip') ?? '降水量'}</dt>
					<dd className="text-2xl font-semibold">{fmt(data?.precip, 1)} mm</dd>
				</div>
			</dl>
		</section>
	);
}

export default ResultCard;
