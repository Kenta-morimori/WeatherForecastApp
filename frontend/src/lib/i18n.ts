'use client';

import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

import enCommon from '../../public/locales/en/common.json';
import jaCommon from '../../public/locales/ja/common.json';

const resources = {
	ja: { common: jaCommon },
	en: { common: enCommon },
} as const;

let initialized = false;

/** 一度だけ初期化。ここでは changeLanguage しない */
export function getI18n() {
	if (!initialized) {
		i18n
			.use(initReactI18next)
			.init({
				resources,
				lng: 'ja',
				fallbackLng: 'ja',
				interpolation: { escapeValue: false },
				defaultNS: 'common',
				ns: ['common'],
				returnEmptyString: false,
			})
			.catch(() => {});
		initialized = true;
	}
	return i18n;
}
