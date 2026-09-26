import { describe, expect, test } from "bun:test";
import {
	findUnownedTodos,
	isVirtualWorkspace,
	ownerSuffix,
	parseSeverity,
	RequestGenerations,
	trailingWhitespace,
} from "../../src/core";

describe("findUnownedTodos", () => {
	test("finds TODO without owner, skips TODO(owner)", () => {
		const text = "a TODO fix\nTODO(ann) done\n// TODO: x TODO";
		expect(findUnownedTodos(text)).toEqual([
			{ line: 0, start: 2, end: 6 },
			{ line: 2, start: 3, end: 7 },
			{ line: 2, start: 11, end: 15 },
		]);
	});
	test("ignores TODOS and xTODO", () => {
		expect(findUnownedTodos("TODOS xTODO")).toEqual([]);
	});
	test("handles CRLF line endings", () => {
		expect(findUnownedTodos("x\r\nTODO")).toEqual([
			{ line: 1, start: 0, end: 4 },
		]);
	});
});

describe("ownerSuffix", () => {
	test("wraps a clean owner", () => {
		expect(ownerSuffix(" ann ")).toBe("(ann)");
	});
	test("rejects owners that would break the syntax", () => {
		expect(() => ownerSuffix("a) rm -rf")).toThrow("invalid owner");
	});
});

test("trailingWhitespace only touches TODO lines", () => {
	expect(trailingWhitespace("TODO x  \nplain  \n")).toEqual([
		{ line: 0, start: 6, end: 8 },
	]);
});

test("parseSeverity falls back to warning", () => {
	expect(parseSeverity("error")).toBe("error");
	expect(parseSeverity("fatal")).toBe("warning");
	expect(parseSeverity(undefined)).toBe("warning");
});

describe("RequestGenerations", () => {
	test("accepts the latest request at the same version", () => {
		const g = new RequestGenerations();
		const gen = g.start("a");
		expect(g.isCurrent("a", gen, 3, 3)).toBe(true);
	});
	test("rejects a result after the document changed", () => {
		const g = new RequestGenerations();
		const gen = g.start("a");
		expect(g.isCurrent("a", gen, 3, 4)).toBe(false);
	});
	test("rejects a superseded request at the same version", () => {
		const g = new RequestGenerations();
		const first = g.start("a");
		g.start("a");
		expect(g.isCurrent("a", first, 3, 3)).toBe(false);
	});
	test("rejects a result for a closed document", () => {
		const g = new RequestGenerations();
		const gen = g.start("a");
		g.forget("a");
		expect(g.isCurrent("a", gen, 3, undefined)).toBe(false);
	});
});

test("isVirtualWorkspace needs every folder off the file scheme", () => {
	expect(isVirtualWorkspace(["vscode-vfs"])).toBe(true);
	expect(isVirtualWorkspace(["vscode-vfs", "file"])).toBe(false);
	expect(isVirtualWorkspace([])).toBe(false);
});
