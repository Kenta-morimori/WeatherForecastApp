"use client";
import type * as React from "react";

type LabelProps = Omit<
	React.LabelHTMLAttributes<HTMLLabelElement>,
	"htmlFor" | "children"
> & {
	htmlFor: string;
	children: React.ReactNode;
};

export function Label({ htmlFor, children, ...props }: LabelProps) {
	return (
		<label
			htmlFor={htmlFor}
			className="mb-1 block text-sm text-gray-700"
			{...props}
		>
			{children}
		</label>
	);
}
export default Label;
