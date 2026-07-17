import { chromium } from "/Users/steve/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs";
import { mkdir } from "node:fs/promises";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";

const root = resolve(".");
const outDir = resolve(root, "output/pdf");
const previewDir = resolve(root, "docs/generated");
await mkdir(outDir, { recursive: true });
await mkdir(previewDir, { recursive: true });

const executablePath = "/Users/steve/Library/Caches/ms-playwright/chromium_headless_shell-1208/chrome-headless-shell-mac-arm64/chrome-headless-shell";
const browser = await chromium.launch({ executablePath });
const page = await browser.newPage({ viewport: { width: 1440, height: 1100 }, deviceScaleFactor: 1 });
await page.goto(pathToFileURL(resolve(root, "docs/index.html")).href, { waitUntil: "networkidle", timeout: 60_000 });
await page.emulateMedia({ media: "print" });
await page.pdf({
  path: resolve(outDir, "CODEX-KEYBORED-Manufacturing-Dossier-RevA2.pdf"),
  format: "A4",
  landscape: false,
  printBackground: true,
  preferCSSPageSize: false,
  margin: { top: "8mm", right: "8mm", bottom: "8mm", left: "8mm" },
});
await page.emulateMedia({ media: "screen" });
await page.screenshot({
  path: resolve(previewDir, "CODEX-KEYBORED-Landing-Full.png"),
  fullPage: true,
});
console.log(JSON.stringify({
  pdf: resolve(outDir, "CODEX-KEYBORED-Manufacturing-Dossier-RevA2.pdf"),
  screenshot: resolve(previewDir, "CODEX-KEYBORED-Landing-Full.png"),
}));
await browser.close();
