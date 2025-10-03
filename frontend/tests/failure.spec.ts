// frontend/tests/failure.spec.ts
import { expect, test } from "@playwright/test";

// 失敗系: geocode がネットワークエラー
test("ja: geocode network failure shows error message", async ({ page }) => {
	await page.route("**/api/geocode/search**", (route) => route.abort("failed"));

	await page.goto("/ja");
	await page.getByLabel("場所を検索").fill("東京駅");
	await page.getByRole("button", { name: "検索" }).click();

	await expect(
		page.getByText(/取得に失敗しました|Failed to fetch/i),
	).toBeVisible();
});

// 失敗系: predict が 5xx
test("ja: predict 502 shows error message", async ({ page }) => {
	await page.route("**/api/geocode/search**", (route) =>
		route.fulfill({
			status: 200,
			contentType: "application/json",
			body: JSON.stringify({
				q: "東京駅",
				source: "live",
				results: [
					{
						name: "東京駅",
						display_name: "東京駅",
						lat: 35.6812,
						lon: 139.7671,
					},
				],
			}),
		}),
	);

	await page.route("**/predict", (route) =>
		route.fulfill({
			status: 502,
			contentType: "text/plain",
			body: "upstream error",
		}),
	);

	await page.goto("/ja");
	await page.getByLabel("場所を検索").fill("東京駅");
	await page.getByRole("button", { name: "検索" }).click();

	await expect(
		page.getByText(/取得に失敗しました|Failed to fetch/i),
	).toBeVisible();
});
