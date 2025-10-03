import { expect, test } from "@playwright/test";

test("ja home renders key UI", async ({ page }) => {
	await page.goto("/ja");

	// Skip link は sr-only → フォーカスすると可視化される
	// まず body にフォーカスを移してから Tab を送る（CI安定化）
	await page.locator("body").click();

	const skipLink = page.getByRole("link", {
		name: /Skip to content|本文へスキップ/i,
	});

	// 最大3回まで Tab を送って可視化を待つ（環境差対策）
	for (let i = 0; i < 3; i++) {
		if (await skipLink.isVisible().catch(() => false)) break;
		await page.keyboard.press("Tab");
	}

	await expect(skipLink).toBeVisible();

	// 検索ラベル（/ja では日本語。念のため英語も許容）
	await expect(page.getByLabel(/場所を検索|Search a place/i)).toBeVisible();
});

test("language toggle switches to English", async ({ page }) => {
	await page.goto("/ja");

	// 可視テキスト（EN/日本語）または aria-label（Language/言語）のどれでも拾う
	const toggle = page.getByRole("button", { name: /Language|言語|EN|日本語/i });

	// クリックと URL 遷移を厳密に同期
	await Promise.all([page.waitForURL(/\/en(\/|$)/), toggle.click()]);

	// 英語UIのラベルが見えること
	await expect(page.getByLabel("Search a place")).toBeVisible();
});
