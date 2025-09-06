import type { Metadata } from 'next';
import { Geist, Geist_Mono } from 'next/font/google';
import './globals.css';

const geistSans = Geist({
	variable: '--font-geist-sans',
	subsets: ['latin'],
});

const geistMono = Geist_Mono({
	variable: '--font-geist-mono',
	subsets: ['latin'],
});

export const metadata: Metadata = {
	title: 'WeatherForecastApp',
	description: "Tomorrow's weather prediction demo",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
	return (
		<html lang="ja">
			<body
				className={`${geistSans.variable} ${geistMono.variable} min-h-dvh bg-background text-foreground antialiased`}
			>
				<div className="container mx-auto max-w-4xl p-4">{children}</div>
			</body>
		</html>
	);
}
