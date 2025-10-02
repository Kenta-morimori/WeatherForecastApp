import { expect, test } from '@playwright/test';

test('ja home renders key UI', async ({ page }) => {
	await page.goto('/ja');
	await expect(page.getByRole('link', { name: 'Skip to content' })).toBeVisible();
	await expect(page.getByLabel('場所を検索')).toBeVisible();
});

test('language toggle switches to English', async ({ page }) => {
	await page.goto('/ja');
	// 実装に合わせてボタンの name は柔軟に
	await page.getByRole('button', { name: /EN|Change language/i }).click();
	await expect(page).toHaveURL(/\/en(\/|$)/);
	await expect(page.getByLabel('Search a place')).toBeVisible();
});
