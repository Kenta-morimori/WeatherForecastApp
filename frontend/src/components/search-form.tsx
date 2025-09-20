'use client';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { cn } from '@/lib/utils';
import { zLocation } from '@/lib/validation';
import { useState } from 'react';
import type { z } from 'zod';

export type SearchFormPayload = z.infer<typeof zLocation>;

export function SearchForm({
	onSubmit,
	className,
}: {
	onSubmit: (payload: SearchFormPayload) => void;
	className?: string;
}) {
	const [form, setForm] = useState<SearchFormPayload>({ name: '', lat: '', lon: '' });
	const [error, setError] = useState<string | null>(null);

	const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
		e.preventDefault();
		const parsed = zLocation.safeParse(form);
		if (!parsed.success) {
			setError(parsed.error.issues[0]?.message ?? '入力エラー');
			return;
		}
		setError(null);
		onSubmit(parsed.data);
	};

	return (
		<Card className={cn(className)}>
			<CardHeader>
				<CardTitle>地点入力</CardTitle>
			</CardHeader>
			<CardContent>
				<form className="grid gap-4" onSubmit={handleSubmit}>
					<div className="grid gap-2">
						<Label htmlFor="name">地名（例: 東京, New York）</Label>
						<Input
							id="name"
							placeholder="任意（※緯度経度の代わりにどちらか一方でOK）"
							value={form.name ?? ''}
							onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
								setForm((s) => ({ ...s, name: e.target.value }))
							}
						/>
					</div>

					<div className="grid grid-cols-1 gap-4 md:grid-cols-2">
						<div className="grid gap-2">
							<Label htmlFor="lat">緯度</Label>
							<Input
								id="lat"
								type="number"
								step="any"
								placeholder="例: 35.681"
								value={form.lat ?? ''}
								onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
									setForm((s) => ({ ...s, lat: e.target.value }))
								}
							/>
						</div>
						<div className="grid gap-2">
							<Label htmlFor="lon">経度</Label>
							<Input
								id="lon"
								type="number"
								step="any"
								placeholder="例: 139.767"
								value={form.lon ?? ''}
								onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
									setForm((s) => ({ ...s, lon: e.target.value }))
								}
							/>
						</div>
					</div>

					{error && <p className="text-sm text-red-600">{error}</p>}

					<div className="flex justify-end">
						<Button type="submit">予測する（モック）</Button>
					</div>
				</form>
			</CardContent>
		</Card>
	);
}
