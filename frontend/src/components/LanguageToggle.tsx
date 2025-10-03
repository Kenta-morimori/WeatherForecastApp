'use client';
import { usePathname, useRouter } from 'next/navigation';
import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';

export function LanguageToggle({ locale }: { locale: 'ja' | 'en' }) {
	const router = useRouter();
	const pathname = usePathname();
	const { t } = useTranslation('common');

	const other = locale === 'ja' ? 'en' : 'ja';
	const nextPath = useMemo(() => {
		if (!pathname) return `/${other}`;
		const parts = pathname.split('/');
		parts[1] = other; // /[locale]/...
		return parts.join('/') || `/${other}`;
	}, [pathname, other]);

	const label = t('toggle_language'); // ← 既存のキーを使用

	return (
		<button
			type="button"
			aria-label={label}
			title={label}
			onClick={() => router.push(nextPath)}
			className="rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white/70 dark:bg-zinc-900/50 px-3 py-1.5 text-sm hover:bg-zinc-50 dark:hover:bg-zinc-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2 dark:focus-visible:ring-offset-zinc-900"
		>
			{locale === 'ja' ? 'EN' : '日本語'}
		</button>
	);
}
