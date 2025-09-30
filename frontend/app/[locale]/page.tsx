'use client';

import Link from 'next/link';
import { useTranslation } from 'react-i18next';

export default function LocaleIndexPage() {
	const { t } = useTranslation('common');
	return (
		<div className="space-y-4">
			<h1 className="text-2xl md:text-3xl font-semibold tracking-tight">{t('title_geo')}</h1>
			<p className="text-zinc-600 dark:text-zinc-300 leading-relaxed">{t('hint_start')}</p>
			<div className="flex gap-3">
				<Link
					href="./geo"
					className="inline-flex items-center rounded-lg px-4 py-2 bg-indigo-600 text-white hover:bg-indigo-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2 dark:focus-visible:ring-offset-zinc-900"
				>
					{t('btn_search')}
				</Link>
				<Link
					href="./forecast"
					className="inline-flex items-center rounded-lg px-4 py-2 border border-zinc-300 dark:border-zinc-700 hover:bg-zinc-50 dark:hover:bg-zinc-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2 dark:focus-visible:ring-offset-zinc-900"
				>
					Forecast
				</Link>
			</div>
		</div>
	);
}
