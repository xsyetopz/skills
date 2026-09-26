import { slug } from "@fixture/util";

const runtime = process.versions.bun
	? `bun ${process.versions.bun}`
	: `node ${process.versions.node}`;
console.log(`${slug("Hello World")} (${runtime})`);
