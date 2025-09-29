// frontend/app/layout.tsx
import './globals.css';
import 'leaflet/dist/leaflet.css'; // ★ ここで読み込む

export const metadata = {
	title: 'Weather Forecast App',
	description: "Tomorrow's weather forecast with AI",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
	return (
		<html lang="ja">
			<body>{children}</body>
		</html>
	);
}
