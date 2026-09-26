import { Config } from "./config.js";
import { Role } from "./roles.js";
import { AccessService } from "./service.js";

export async function main(): Promise<void> {
	console.log(`listening on ${Config.port} in ${Config.region}`);
	const { memoryRepo } = await import("./repo.js");
	const access = new AccessService(memoryRepo());
	console.log(`refund 1: ${access.canRefund(1)}, refund 2: ${access.canRefund(2)}, role 1 is ${Role[1]}`);
}

await main();
