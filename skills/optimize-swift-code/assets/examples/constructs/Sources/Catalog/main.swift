// Catalog entry point.
//   Catalog verify   oracles + allocation/ARC/hash-count assertions
//   Catalog smoke    run every pair once (no timing)
//   Catalog time [filter]   ContinuousClock medians for each pair
import CCount
import Constructs
import Darwin

let arguments = CommandLine.arguments.dropFirst()
let mode = arguments.first ?? "verify"
// The size comes from argv so the optimizer cannot constant-fold inputs.
let n = CommandLine.arguments.count > 99 ? 1 : 1000

switch mode {
case "verify", "smoke":
  guard ccount_install_malloc() == 0 else {
    print("FAIL could not install the malloc counter")
    exit(1)
  }
  ccount_install_arc()
  collectionChecks(n)
  valueChecks(n)
  dispatchChecks(n)
  stringChecks(n)
  await concurrencyChecks()
  if failures > 0 {
    print("\(failures) check(s) failed")
    exit(1)
  }
  print(
    mode == "smoke"
      ? "SMOKE PASSED: every pair ran; not a timing result."
      : "VERIFY PASSED")
case "time":
  await runTimings(filter: arguments.dropFirst().first ?? "")
default:
  print("usage: Catalog verify|smoke|time [filter]")
  exit(2)
}
