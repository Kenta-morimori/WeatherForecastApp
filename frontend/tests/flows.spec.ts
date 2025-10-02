import { expect, test } from '@playwright/test';

// 1件ヒット → 自動で doPredict まで
test('ja: 1 hit -> auto predict', async ({ page }) => {
	await page.route('**/api/geocode/search**', (route) =>
		route.fulfill({
			status: 200,
			contentType: 'application/json',
			body: JSON.stringify({
				q: '東京駅',
				source: 'live',
				results: [{ name: '東京駅', display_name: '東京駅', lat: 35.6812, lon: 139.7671 }],
			}),
		}),
	);
	await page.route('**/predict', (route) =>
		route.fulfill({
			status: 200,
			contentType: 'application/json',
			body: JSON.stringify({
				backend: 'regression',
				date_d0: '2025-10-02',
				date_d1: '2025-10-03',
				prediction: { d1_mean: 22.3, d1_min: 18.0, d1_max: 26.1, d1_prec: 3.2 },
			}),
		}),
	);

	await page.goto('/ja');
	await page.getByLabel('場所を検索').fill('東京駅');
	await page.getByRole('button', { name: '検索' }).click();

	await expect(page.getByText(/明日の予測|Tomorrow/)).toBeVisible();
});

// 複数ヒット → セレクトで決定 → 予測
test('ja: multi hits -> select -> predict', async ({ page }) => {
	await page.route('**/api/geocode/search**', (route) =>
		route.fulfill({
			status: 200,
			contentType: 'application/json',
			body: JSON.stringify({
				q: '品川',
				source: 'live',
				results: [
					{ name: '品川駅', display_name: '品川駅', lat: 35.6285, lon: 139.7386 },
					{ name: '北品川駅', display_name: '北品川駅', lat: 35.6198, lon: 139.7376 },
				],
			}),
		}),
	);
	await page.route('**/predict', (route) =>
		route.fulfill({
			status: 200,
			contentType: 'application/json',
			body: JSON.stringify({
				backend: 'regression',
				date_d0: '2025-10-02',
				date_d1: '2025-10-03',
				prediction: { d1_mean: 20.0, d1_min: 17.0, d1_max: 24.0, d1_prec: 1.2 },
			}),
		}),
	);

	await page.goto('/ja');
	await page.getByLabel('場所を検索').fill('品川');
	await page.getByRole('button', { name: '検索' }).click();

	const list = page.locator('select#geocode-results');
	await list.waitFor(); // セレクトの出現を待機
	await list.selectOption({ index: 0 }); // ← これで onChange が必ず発火（Enter/Spaceより堅い）

	// 予測結果の表示を待つ
	await expect(page.getByText(/明日の予測|Tomorrow/)).toBeVisible();
});
