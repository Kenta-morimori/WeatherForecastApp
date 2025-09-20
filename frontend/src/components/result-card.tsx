'use client';
import React from 'react';

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
	if ('locationLabel' in props) {
		const { locationLabel, tempMean, tempMin, tempMax, precipMm } = props;
		return (
			<div className="w-full rounded-2xl border p-4 shadow">
				<div className="mb-2 text-sm text-gray-500">{locationLabel}</div>
				<div className="grid grid-cols-2 gap-4 text-sm sm:text-base">
					<div className="rounded-2xl bg-gray-100 p-3">
						<div className="opacity-70">最高</div>
						<div className="text-2xl font-semibold">{fmt(tempMax)}℃</div>
					</div>
					<div className="rounded-2xl bg-gray-100 p-3">
						<div className="opacity-70">最低</div>
						<div className="text-2xl font-semibold">{fmt(tempMin)}℃</div>
					</div>
					<div className="rounded-2xl bg-gray-100 p-3">
						<div className="opacity-70">平均</div>
						<div className="text-2xl font-semibold">{fmt(tempMean)}℃</div>
					</div>
					<div className="rounded-2xl bg-gray-100 p-3">
						<div className="opacity-70">降水量</div>
						<div className="text-2xl font-semibold">{fmt(precipMm, 1)} mm</div>
					</div>
				</div>
			</div>
		);
	}

	const { title = '', data } = props;
	return (
		<div className="w-full rounded-2xl border p-4 shadow">
			{title && <div className="mb-2 text-xl">{title}</div>}
			<div className="grid grid-cols-2 gap-4 text-sm sm:text-base">
				<div className="rounded-2xl bg-gray-100 p-3">
					<div className="opacity-70">最高</div>
					<div className="text-2xl font-semibold">{fmt(data?.max)}℃</div>
				</div>
				<div className="rounded-2xl bg-gray-100 p-3">
					<div className="opacity-70">最低</div>
					<div className="text-2xl font-semibold">{fmt(data?.min)}℃</div>
				</div>
				<div className="rounded-2xl bg-gray-100 p-3">
					<div className="opacity-70">降水確率</div>
					<div className="text-2xl font-semibold">{toPct(data?.precip_prob)}</div>
				</div>
				<div className="rounded-2xl bg-gray-100 p-3">
					<div className="opacity-70">降水量</div>
					<div className="text-2xl font-semibold">{fmt(data?.precip, 1)} mm</div>
				</div>
			</div>
		</div>
	);
}

export default ResultCard;
