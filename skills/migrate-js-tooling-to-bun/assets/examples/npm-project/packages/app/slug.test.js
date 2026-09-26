import { describe, expect, it, mock } from "bun:test";
import { slug } from "@fixture/util";

describe("slug", () => {
	it("lowercases and joins words", () => {
		expect(slug("  Hello   World ")).toBe("hello-world");
	});

	it("supports jest-style mocks", () => {
		const fn = mock((x) => x * 2);
		fn(2);
		expect(fn).toHaveBeenCalledTimes(1);
	});
});
