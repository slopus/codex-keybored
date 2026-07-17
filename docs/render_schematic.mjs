import { chromium } from "/Users/steve/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs";
import { mkdir } from "node:fs/promises";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";

const root = resolve(".");
const out = resolve(root, "electronics/production/schematic");
await mkdir(out, { recursive: true });
const executablePath = "/Users/steve/Library/Caches/ms-playwright/chromium_headless_shell-1208/chrome-headless-shell-mac-arm64/chrome-headless-shell";
const browser = await chromium.launch({ executablePath });
const page = await browser.newPage({ viewport: { width: 1500, height: 1010 }, deviceScaleFactor: 1 });
await page.goto(pathToFileURL(resolve(root, "docs/schematic.html")).href, { waitUntil: "networkidle" });
await page.emulateMedia({ media: "print" });
await page.pdf({
  path: resolve(out, "CODEX_KEYBORED_RevA2_schematic.pdf"),
  format: "A3",
  landscape: true,
  printBackground: true,
  margin: { top: "0", right: "0", bottom: "0", left: "0" },
});
await page.emulateMedia({ media: "screen" });
const sheets = page.locator(".sheet");
for (let i = 0; i < await sheets.count(); i++) {
  await sheets.nth(i).screenshot({ path: resolve(out, `CODEX_KEYBORED_schematic_${i + 1}.png`) });
}
await browser.close();
console.log(JSON.stringify({ pdf: resolve(out, "CODEX_KEYBORED_RevA2_schematic.pdf"), pages: 3 }));
