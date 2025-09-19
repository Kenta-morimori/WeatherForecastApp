'use client';
import type * as React from 'react';
export function Input(props: React.InputHTMLAttributes<HTMLInputElement>) {
	return (
		<input
			className="w-full rounded-2xl border border-gray-300 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-gray-800"
			{...props}
		/>
	);
}
export default Input;
