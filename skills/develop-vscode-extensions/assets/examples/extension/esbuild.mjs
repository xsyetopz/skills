// Bundles one CommonJS file per extension host. "vscode" stays external:
// the extension host provides it at runtime.
import * as esbuild from "esbuild";

const production = process.argv.includes("--production");
const common = {
	bundle: true,
	format: "cjs",
	minify: production,
	sourcemap: !production,
	sourcesContent: false,
	external: ["vscode"],
	logLevel: "warning",
};

await esbuild.build({
	...common,
	entryPoints: ["src/extension.node.ts"],
	platform: "node",
	target: "node16",
	outfile: "dist/node/extension.js",
});
await esbuild.build({
	...common,
	entryPoints: ["src/extension.web.ts"],
	platform: "browser",
	target: "es2022",
	outfile: "dist/web/extension.js",
});
