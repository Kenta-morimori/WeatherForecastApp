"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";
import { zLocation } from "@/lib/validation";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import type { z } from "zod";

export type SearchFormPayload = z.infer<typeof zLocation>;

export function SearchForm({
	onSubmit,
	className,
}: {
	onSubmit: (payload: SearchFormPayload) => void;
	className?: string;
}) {
	const { t } = useTranslation("common");

	const [form, setForm] = useState<SearchFormPayload>({
		name: "",
		lat: "",
		lon: "",
	});
	const [error, setError] = useState<string | null>(null);

	const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
		e.preventDefault();
		const parsed = zLocation.safeParse(form);
		if (!parsed.success) {
			setError(parsed.error.issues[0]?.message ?? t("error_fetch"));
			return;
		}
		setError(null);
		onSubmit(parsed.data);
	};

	return (
		<Card className={cn(className)}>
			<CardHeader>
				<CardTitle>{t("title_geo")}</CardTitle>
			</CardHeader>
			<CardContent>
				<form
					className="grid gap-4"
					onSubmit={handleSubmit}
					aria-describedby={error ? "form-error" : undefined}
				>
					<div className="grid gap-2">
						<Label htmlFor="name">{t("search_label")}</Label>
						<Input
							id="name"
							placeholder={t("placeholder_search")}
							value={form.name ?? ""}
							onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
								setForm((s) => ({ ...s, name: e.target.value }))
							}
						/>
					</div>

					<div className="grid grid-cols-1 gap-4 md:grid-cols-2">
						<div className="grid gap-2">
							<Label htmlFor="lat">{t("label_lat") ?? "緯度"}</Label>
							<Input
								id="lat"
								type="number"
								step="any"
								placeholder={t("placeholder_lat") ?? "例: 35.681"}
								value={form.lat ?? ""}
								onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
									setForm((s) => ({ ...s, lat: e.target.value }))
								}
							/>
						</div>
						<div className="grid gap-2">
							<Label htmlFor="lon">{t("label_lon") ?? "経度"}</Label>
							<Input
								id="lon"
								type="number"
								step="any"
								placeholder={t("placeholder_lon") ?? "例: 139.767"}
								value={form.lon ?? ""}
								onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
									setForm((s) => ({ ...s, lon: e.target.value }))
								}
							/>
						</div>
					</div>

					{error && (
						<p
							id="form-error"
							className="text-sm text-red-600"
							role="alert"
							aria-live="assertive"
						>
							{error}
						</p>
					)}

					<div className="flex justify-end">
						<Button type="submit">
							{t("btn_predict") ?? "予測する（モック）"}
						</Button>
					</div>
				</form>
			</CardContent>
		</Card>
	);
}
