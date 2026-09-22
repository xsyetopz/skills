# Bundled resource map for Behavioral Testing

Use this map to locate resources for behavioral test. Load only the item
required by the current decision. When an example is a native project, preserve
its manifest, lockfile, descriptors, fixtures, and relative layout.

| Path | Role and evidence boundary |
| --- | --- |
| `assets/hdl-counter/counter.sv` | SystemVerilog implementation or testbench |
| `assets/hdl-counter/counter_equivalent.sv` | Conforming alternative used to show the check accepts more than one implementation. |
| `assets/hdl-counter/counter_faulty.sv` | Deliberately defective fixture used to prove the check rejects a relevant fault; never copy into production. |
| `assets/hdl-counter/counter_tb.sv` | SystemVerilog implementation or testbench |
| `assets/hdl-counter/verify.sh` | Deterministic verifier/runner; inspect supported arguments and evidence limits before use. |
| `assets/oracle-example.py` | Python implementation, test, or deterministic helper |
| `assets/rename-contract/rename_operation.py` | Python implementation, test, or deterministic helper |
| `assets/rename-contract/test_rename_operation.py` | Executable test or fault-discrimination fixture; run with the neighboring project configuration. |

## Use rules

- Use a script only for its documented behavioral test transformation. Inspect
  arguments, stdout, stderr, exit status, and created files.
- Assets contain behavioral test templates, fixtures, or complete example
  projects. Preserve required manifests and relative paths when copying them.
- A deliberately faulty fixture demonstrates fault discrimination; it is not a
  production recommendation.
- A passing bundled example establishes only its own contract in the executed
  environment; it does not prove the target system.
