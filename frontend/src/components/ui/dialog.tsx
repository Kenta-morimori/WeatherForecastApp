"use client";
import type * as React from "react";

export function Dialog({
	open,
	onOpenChange,
	children,
}: {
	open: boolean;
	onOpenChange: (v: boolean) => void;
	children: React.ReactNode;
}) {
	if (!open) return null;

	function onBackdropClick() {
		onOpenChange(false);
	}
	function onBackdropKeyDown(e: React.KeyboardEvent<HTMLDivElement>) {
		// マウスだけでなくキーボードでも閉じられるように
		if (e.key === "Escape" || e.key === "Enter" || e.key === " ") {
			onOpenChange(false);
		}
	}
	function onContentKeyDown(e: React.KeyboardEvent<HTMLDialogElement>) {
		if (e.key === "Escape") onOpenChange(false);
	}

	return (
		<div
			className="fixed inset-0 z-50 grid place-items-center bg-black/50"
			onClick={onBackdropClick}
			onKeyDown={onBackdropKeyDown}
			aria-modal="true"
		>
			<dialog
				open
				className="w-[min(92vw,560px)] rounded-2xl bg-white p-4"
				onClick={(e) => e.stopPropagation()}
				onKeyDown={onContentKeyDown}
			>
				{children}
			</dialog>
		</div>
	);
}

export function DialogContent({ children }: { children: React.ReactNode }) {
	return <div className="space-y-3">{children}</div>;
}
export function DialogHeader({ children }: { children: React.ReactNode }) {
	return <div className="mb-2">{children}</div>;
}
export function DialogFooter({ children }: { children: React.ReactNode }) {
	return <div className="mt-4 flex justify-end gap-2">{children}</div>;
}
export function DialogTitle({ children }: { children: React.ReactNode }) {
	return <h2 className="text-lg font-semibold">{children}</h2>;
}
