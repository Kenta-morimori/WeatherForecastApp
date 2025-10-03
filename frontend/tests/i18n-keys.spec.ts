import fs from "node:fs";
import path from "node:path";
import { expect, test } from "@playwright/test";

function flatKeys(obj: unknown, prefix = ""): string[] {
	if (!obj || typeof obj !== "object") return [prefix.slice(0, -1)];
	return Object.entries(obj as Record<string, unknown>).flatMap(([k, v]) =>
		typeof v === "object" && v !== null
			? flatKeys(v, `${prefix}${k}.`)
			: `${prefix}${k}`,
	);
}

test("public/locales/ja/en/common.json keys are identical", async () => {
	const jaPath = path.join(
		__dirname,
		"..",
		"public",
		"locales",
		"ja",
		"common.json",
	);
	const enPath = path.join(
		__dirname,
		"..",
		"public",
		"locales",
		"en",
		"common.json",
	);
	const ja = JSON.parse(fs.readFileSync(jaPath, "utf8"));
	const en = JSON.parse(fs.readFileSync(enPath, "utf8"));

	const jaKeys = flatKeys(ja).sort();
	const enKeys = flatKeys(en).sort();

	expect(jaKeys).toEqual(enKeys);
});
