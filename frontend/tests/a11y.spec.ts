import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';

test('a11y: /ja has no serious WCAG 2A/2AA violations', async ({ page }) => {
	await page.goto('/ja');

	const results = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa']).analyze();

	// デバッグしたいときに可視化
	if (results.violations.length) {
		console.log(JSON.stringify(results.violations, null, 2));
	}
	expect(results.violations).toEqual([]);
});

test('a11y: /en has no serious WCAG 2A/2AA violations', async ({ page }) => {
	await page.goto('/en');

	const results = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa']).analyze();

	if (results.violations.length) {
		console.log(JSON.stringify(results.violations, null, 2));
	}
	expect(results.violations).toEqual([]);
});
