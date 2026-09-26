// Namespaces: two modules both export `normalize`. Namespace imports keep
// each call site explicit about which one runs.
import assert from "node:assert/strict";
import * as text from "./text.ts";
import * as url from "./url.ts";

assert.deepEqual(text.parse(" A, b ,,C "), ["a", "b", "c"]);
assert.equal(url.normalize("HTTPS://Example.com"), "https://example.com/");
assert.equal(text.normalize(" X "), "x");
console.log("namespaces: text.normalize and url.normalize coexist");
