# Verification and claim evidence for Behavioral Testing

Select evidence that can discriminate the claimed property of the behavioral
test. Run the smallest sufficient check first. Broaden only when another
contract boundary changed.

| Claim | Sufficient evidence | Not sufficient by itself |
| --- | --- | --- |
| TDD red observed | Test executed before behavior implementation and failed for the intended missing/incorrect behavior. | Later running a mutant or deleting code. |
| Test oracle is independent | Expectation from contract/reference/model independent of production path. | Expected value computed by same algorithm. |
| Test discriminates defect | Relevant faulty implementation fails and conforming implementation passes. | Test count or coverage percentage. |
| Integration works | Actual components/protocol/storage/host exercised with observed contract. | Mock expectations. |
| Firmware/HDL works in simulation | Target sources built/elaborated and simulator observed specified signals/state. | Syntax check only. |
| Physical target works | Identified device/firmware/fixture/instrument run with authorized conditions and observations. | Simulation or host test. |
| Suite is stable | Repeated/controlled runs and root cause for prior flake where relevant. | One pass. |

## Command patterns

```sh
python3 -m unittest assets/rename-contract/test_rename_operation.py
# HDL, when Icarus Verilog is installed:
sh assets/hdl-counter/verify.sh
```

These examples demonstrate their documented contracts only. Missing simulator
means the HDL case is unexecuted, not passed.

## Result reporting

For the behavioral test, separate authored checks, executed checks, static
analysis, simulation, host/integration execution, production observations,
skips, and unavailable checks. Include useful failure output. A green check
establishes only the property that it can discriminate.
