'use client';

import { getI18n } from '@/lib/i18n';
import { useEffect } from 'react';
import { I18nextProvider } from 'react-i18next';

/**
 * クライアント境界でのみ言語切替を行う（render 中に setState しない）
 */
export function ClientI18nProvider({
	locale,
	children,
}: {
	locale: 'ja' | 'en';
	children: React.ReactNode;
}) {
	const i18n = getI18n();

	useEffect(() => {
		if (i18n.language !== locale) {
			void i18n.changeLanguage(locale);
		}
	}, [i18n, locale]);

	return <I18nextProvider i18n={i18n}>{children}</I18nextProvider>;
}
