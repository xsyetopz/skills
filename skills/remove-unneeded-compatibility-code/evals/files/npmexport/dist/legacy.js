// Deprecated since 3.0: use toMeters from "@acme/units".
import { toMeters } from "./index.js";

export function convert(value, unit) {
  console.warn("@acme/units/legacy is deprecated; use toMeters");
  return toMeters(value, unit);
}
