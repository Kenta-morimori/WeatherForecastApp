import type { Config } from 'tailwindcss';

export default {
	// ".dark" セレクタを明示的に使う運用ならこのままでOK
	darkMode: ['class', '.dark'],
	// ← ここを広げる（App Router & components を網羅）
	content: [
		'./app/**/*.{ts,tsx,js,jsx,mdx}',
		'./src/**/*.{ts,tsx,js,jsx,mdx}',
		'./components/**/*.{ts,tsx,js,jsx,mdx}',
	],
	theme: {
		extend: {
			colors: {
				background: 'hsl(0 0% 100%)',
				foreground: 'hsl(222.2 47.4% 11.2%)',
				primary: { DEFAULT: 'hsl(221.2 83.2% 53.3%)', foreground: 'hsl(210 40% 98%)' },
				card: { DEFAULT: 'hsl(0 0% 100%)', foreground: 'hsl(222.2 47.4% 11.2%)' },
				input: 'hsl(214.3 31.8% 91.4%)',
				ring: 'hsl(221.2 83.2% 53.3%)',
				muted: { DEFAULT: 'hsl(210 40% 96.1%)', foreground: 'hsl(215.4 16.3% 46.9%)' },
				destructive: 'hsl(0 84.2% 60.2%)',
			},
			borderRadius: { xl: '0.75rem' },
			container: { center: true, padding: '1rem' },
		},
	},
	plugins: [],
} satisfies Config;
