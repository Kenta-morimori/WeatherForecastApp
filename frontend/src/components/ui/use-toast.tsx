'use client';
import * as React from 'react';

type Toast = {
	id: number;
	title: string;
	description?: string;
	variant?: 'default' | 'destructive';
};
const ToastCtx = React.createContext<{ toast: (t: Omit<Toast, 'id'>) => void } | null>(null);

export function Toaster() {
	const [items, setItems] = React.useState<Toast[]>([]);
	React.useEffect(() => {
		const timer = setInterval(() => {
			setItems((xs) => xs.slice(1));
		}, 3000);
		return () => clearInterval(timer);
	}, []);
	return (
		<div className="fixed right-4 top-4 z-50 space-y-2">
			{items.map((t) => (
				<div
					key={t.id}
					className={`min-w-[260px] rounded-2xl px-4 py-3 text-sm shadow-lg ${
						t.variant === 'destructive' ? 'bg-red-600 text-white' : 'bg-gray-900 text-white'
					}`}
				>
					<div className="font-semibold">{t.title}</div>
					{t.description && <div className="opacity-90">{t.description}</div>}
				</div>
			))}
		</div>
	);
}

export function ToastProvider({ children }: { children: React.ReactNode }) {
	const [seq, setSeq] = React.useState(0);
	const [items, setItems] = React.useState<Toast[]>([]);
	const value = React.useMemo(
		() => ({
			toast: (t: Omit<Toast, 'id'>) => {
				setSeq((s) => s + 1);
				setItems((xs) => [...xs, { id: seq, ...t }]);
				setTimeout(() => setItems((xs) => xs.slice(1)), 3000);
			},
		}),
		[seq],
	);
	return (
		<ToastCtx.Provider value={value}>
			{children}
			{/* Render toasts */}
			<div className="fixed right-4 top-4 z-50 space-y-2">
				{items.map((t) => (
					<div
						key={t.id}
						className={`min-w-[260px] rounded-2xl px-4 py-3 text-sm shadow-lg ${
							t.variant === 'destructive' ? 'bg-red-600 text-white' : 'bg-gray-900 text-white'
						}`}
					>
						<div className="font-semibold">{t.title}</div>
						{t.description && <div className="opacity-90">{t.description}</div>}
					</div>
				))}
			</div>
		</ToastCtx.Provider>
	);
}

export function useToast() {
	const ctx = React.useContext(ToastCtx);
	if (!ctx) {
		// Provider外でも落とさないフォールバック
		return { toast: () => {} };
	}
	return ctx;
}
