import { expect, test } from "bun:test";
import { hasRoute } from "../src/index";

test("known route", () => {
  expect(hasRoute("/health")).toBe(true);
});
