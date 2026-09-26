// Stand-in for a heavy third-party SDK: evaluating it is slow (it builds
// lookup tables and opens a connection pool in the real package).
const started = performance.now();
let table = 0;
for (let i = 0; i < 30_000_000; i++) table = (table + i * 31) % 1_000_003;
console.log(`analytics-sdk evaluated (${Math.round(performance.now() - started)} ms)`);

export class AnalyticsClient {
	track(event: string, props: Record<string, unknown>): void {
		console.log(`track ${event} ${JSON.stringify(props)} ${table > -1}`);
	}
}
