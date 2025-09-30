// app/[locale]/layout.tsx
import { ensureI18n } from '@/lib/i18n';
import type { Metadata } from 'next';
import { I18nextProvider } from 'react-i18next';
import './globals.css';
import { LanguageToggle } from '@/components/LanguageToggle';

export const metadata: Metadata = {
	title: 'WeatherForecastApp',
	description: 'Search a place & get forecast powered by AI',
};

export default function LocaleLayout({
	children,
	params,
}: {
	children: React.ReactNode;
	params: { locale: 'ja' | 'en' };
}) {
	const i18n = ensureI18n(params.locale);

	return (
		<html lang={params.locale} className="h-full">
			<body className="min-h-screen bg-[radial-gradient(ellipse_at_top,rgba(99,102,241,0.10),transparent_50%),linear-gradient(to_bottom,white,white)] text-zinc-800 antialiased dark:bg-zinc-950 dark:text-zinc-100">
				{/* Skip link */}
				<a
					href="#main"
					className="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-50 focus:px-3 focus:py-2 focus:rounded-md focus:bg-white focus:text-zinc-900 focus:shadow-lg focus:ring-2 focus:ring-indigo-500 dark:focus:bg-zinc-900 dark:focus:text-white"
				>
					Skip to content
				</a>

				<I18nextProvider i18n={i18n}>
					<header className="sticky top-0 z-40 backdrop-blur supports-[backdrop-filter]:bg-white/60 dark:supports-[backdrop-filter]:bg-zinc-900/60 border-b border-zinc-200/60 dark:border-zinc-800/60">
						<div className="mx-auto max-w-3xl px-6 py-3 flex items-center justify-between">
							<div className="text-lg font-semibold tracking-tight">WeatherForecastApp</div>
							<nav aria-label="Global" className="flex items-center gap-3">
								<LanguageToggle locale={params.locale} />
							</nav>
						</div>
					</header>

					<main id="main" className="mx-auto max-w-3xl px-6 py-8 space-y-6">
						<section
							className="rounded-2xl border border-zinc-200/60 dark:border-zinc-800/60 bg-white/70 dark:bg-zinc-900/50 shadow-[0_1px_24px_-8px_rgba(0,0,0,0.25)]"
							aria-label="App content"
						>
							<div className="p-6 md:p-8">{children}</div>
						</section>
					</main>

					<footer className="mx-auto max-w-3xl px-6 py-8 text-sm text-zinc-500 dark:text-zinc-400">
						© WeatherForecastApp · Map tiles: © OpenStreetMap contributors
					</footer>
				</I18nextProvider>
			</body>
		</html>
	);
}
