import './globals.css';
import { ToastProvider } from '@/components/ui/use-toast';
import type { ReactNode } from 'react';

export default function RootLayout({ children }: { children: ReactNode }) {
	return (
		<html lang="ja">
			<body>
				<ToastProvider>{children}</ToastProvider>
			</body>
		</html>
	);
}
