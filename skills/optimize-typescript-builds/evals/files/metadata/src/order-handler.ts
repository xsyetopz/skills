import { Inject, Injectable } from "./di.js";
import { ANALYTICS } from "./tokens.js";
import { AnalyticsClient } from "./vendor/analytics-sdk.js";

@Injectable()
export class OrderHandler {
	constructor(@Inject(ANALYTICS) private readonly analytics: AnalyticsClient) {}

	handle(orderId: number): string {
		this.analytics.track("order", { orderId });
		return `handled order ${orderId}`;
	}
}
