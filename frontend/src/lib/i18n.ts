'use client';

import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

import enCommon from '../../public/locales/en/common.json';
// 直輸入（bundle化）で安定動作。必要に応じてファイル分割も可
import jaCommon from '../../public/locales/ja/common.json';

const resources = {
	ja: { common: jaCommon },
	en: { common: enCommon },
} as const;

export function ensureI18n(locale: 'ja' | 'en') {
	if (!i18n.isInitialized) {
		i18n
			.use(initReactI18next)
			.init({
				resources,
				lng: locale,
				fallbackLng: 'ja',
				interpolation: { escapeValue: false },
				defaultNS: 'common',
				ns: ['common'],
				returnEmptyString: false,
			})
			.catch(() => {});
	} else if (i18n.language !== locale) {
		i18n.changeLanguage(locale).catch(() => {});
	}
	return i18n;
}
