"use client";
import type * as React from "react";

type Props = React.ButtonHTMLAttributes<HTMLButtonElement> & {
	variant?: "default" | "destructive";
};
export function Button({
	className = "",
	variant = "default",
	...props
}: Props) {
	const base =
		"inline-flex items-center justify-center rounded-2xl px-4 py-2 text-sm font-medium transition";
	const color =
		variant === "destructive"
			? "bg-red-600 text-white hover:bg-red-700"
			: "bg-gray-900 text-white hover:bg-gray-800";
	return <button className={`${base} ${color} ${className}`} {...props} />;
}
export default Button;
