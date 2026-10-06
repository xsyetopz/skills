import { expect, test } from "bun:test";

import { total } from "../src/total.ts";

test("total adds prices", () => {
  expect(total([1, 2, 3])).toBe(6);
});
