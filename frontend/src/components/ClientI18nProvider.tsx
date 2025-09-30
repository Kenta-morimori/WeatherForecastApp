'use client';

import { ensureI18n } from '@/lib/i18n';
import { I18nextProvider } from 'react-i18next';

export function ClientI18nProvider({
	locale,
	children,
}: {
	locale: 'ja' | 'en';
	children: React.ReactNode;
}) {
	const i18n = ensureI18n(locale);
	return <I18nextProvider i18n={i18n}>{children}</I18nextProvider>;
}
