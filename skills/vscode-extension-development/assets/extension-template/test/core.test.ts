import assert from "node:assert/strict";
import { test } from "node:test";
import { greeting } from "../src/core.ts";

test("greeting trims names", () => {
  assert.equal(greeting(" editor "), "Hello, editor.");
});
