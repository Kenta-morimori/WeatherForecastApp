// app/layout.tsx
import "./globals.css";

export default function RootLayout({
	children,
}: { children: React.ReactNode }) {
	return (
		<html lang="ja" className="h-full">
			<body className="min-h-screen">{children}</body>
		</html>
	);
}
