#!/usr/bin/env bun

import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

const checkOnly = process.argv.includes("--check");
const outdir = checkOnly
  ? await mkdtemp(join(tmpdir(), "vscode-extension-build-"))
  : "dist";

async function build(entrypoint, target) {
  const result = await Bun.build({
    entrypoints: [entrypoint],
    outdir,
    target,
    format: "cjs",
    minify: true,
    sourcemap: "external",
    external: ["vscode"],
    naming: "[name].[ext]",
  });

  if (!result.success) {
    for (const log of result.logs) {
      console.error(log);
    }
    throw new Error(`Bun.build failed for ${entrypoint}`);
  }
}

try {
  if (!checkOnly) {
    await rm(outdir, { recursive: true, force: true });
  }

  await build("src/extension.ts", "node");
} finally {
  if (checkOnly) {
    await rm(outdir, { recursive: true, force: true });
  }
}
