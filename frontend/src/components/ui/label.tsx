import { cn } from '@/lib/utils';
import * as React from 'react';

export type LabelProps = React.LabelHTMLAttributes<HTMLLabelElement>;

export const Label = React.forwardRef<HTMLLabelElement, LabelProps>(
	({ className, children, ...props }, ref) => (
		// biome-ignore lint/a11y/noLabelWithoutControl: this wrapper forwards `htmlFor` and/or wraps a control as children.
		<label
			ref={ref}
			className={cn(
				'text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70',
				className,
			)}
			{...props}
		>
			{children}
		</label>
	),
);
Label.displayName = 'Label';
