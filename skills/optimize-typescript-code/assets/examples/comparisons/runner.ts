import { run, verify } from "./pairs.ts";

const args = process.argv.slice(2);
if (args.length === 1 && args[0] === "verify") {
	console.log(`PASS ${verify()} checks`);
} else if (args.length === 3) {
	console.log(JSON.stringify(run(args[0], Number(args[1]), Number(args[2]))));
} else {
	throw new Error("usage: node --experimental-strip-types runner.ts verify | baseline|candidate CASE SIZE");
}
