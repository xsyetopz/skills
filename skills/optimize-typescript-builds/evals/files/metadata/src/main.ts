import { register, resolve } from "./di.js";
import { OrderHandler } from "./order-handler.js";
import { ANALYTICS } from "./tokens.js";

declare const process: { env: Record<string, string | undefined> };

// Analytics is only loaded when enabled; otherwise a no-op client is used.
if (process.env.ANALYTICS === "1") {
	const { AnalyticsClient } = await import("./vendor/analytics-sdk.js");
	register(ANALYTICS, () => new AnalyticsClient());
} else {
	register(ANALYTICS, () => ({ track: () => {} }));
}

console.log(resolve(OrderHandler).handle(42));
