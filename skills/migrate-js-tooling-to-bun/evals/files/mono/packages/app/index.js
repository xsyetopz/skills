import { slug } from "@acme/util";

const runtime = process.versions.bun ? `bun ${process.versions.bun}` : `node ${process.version}`;
console.log(`${slug("  Hello, Acme World! ")} (runtime: ${runtime})`);
