import { readFile, writeFile } from "node:fs/promises";
import { resolve } from "node:path";

const root = resolve(".");
const sourcePath = resolve(root, "docs/index.html");
const outputPath = resolve(root, "index.html");

const source = await readFile(sourcePath, "utf8");
const generated = source
  .replace(
    "<!doctype html>",
    "<!doctype html>\n<!-- Generated from docs/index.html by docs/build_root.mjs. -->",
  )
  .replace(
    "<title>CODEX KEYBORED / Work Loafer manufacturing dossier</title>",
    "<title>CODEX KEYBORED / Work Loafer manufacturing dossier</title>\n  <link rel=\"canonical\" href=\"https://happy.engineering/codex-keybored/\">",
  )
  .replaceAll('src="assets/', 'src="docs/assets/')
  .replaceAll('src="../', 'src="')
  .replaceAll('href="../', 'href="');

await writeFile(outputPath, generated);
console.log(JSON.stringify({ source: sourcePath, output: outputPath }));
