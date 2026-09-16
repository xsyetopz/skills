# Bundled resource catalog

Use this catalog to locate the exact skill-local files needed for the task. Do
not load every source file into context by default. Preserve complete native
project directories—including manifests, locks, descriptors, and fixtures—when
copying or executing an example.

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

- `scripts/` contains executable helpers for the skill workflow. Run a helper
  only with documented arguments and inspect stdout/stderr and exit status.
- `assets/` contains templates, complete example projects, fixtures, and other
  material copied, adapted, or executed as part of the task. Assets are not
  instructions by themselves.
- Deliberately faulty fixtures exist only to demonstrate fault discrimination.
  Never present them as recommended implementation code.
- A compiled or passing bundled example establishes only its own contract in the
  executed environment. It does not prove the target repository or production
  system correct.
