import { strictEqual } from "node:assert";
import { test } from "node:test";
import { slug } from "@acme/util";

test("slug collapses punctuation", () => {
	strictEqual(slug("  Hello, Acme World! "), "hello-acme-world");
});

test("slug of empty text", () => {
	strictEqual(slug("   "), "");
});
