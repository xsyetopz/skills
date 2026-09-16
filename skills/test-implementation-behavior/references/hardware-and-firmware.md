# Verify hardware and firmware behavior

Use this reference when the claimed result depends on a simulator, emulator,
firmware image, board, peripheral, or instrument. Preserve the actual project's
runner, target configuration, toolchain, testbench, and fixture interfaces. Do
not introduce a universal device abstraction to run one test.

## Select the observation boundary

| Required property | Appropriate observation | What it does not establish |
| --- | --- | --- |
| Host algorithm or parser | Existing host unit/property tests | Target interrupt, timing, or peripheral behavior |
| Firmware control flow | Identified instruction/peripheral simulator or target | A simulated peripheral is not the physical part |
| HDL logic or protocol | HDL testbench observing ports and clock/reset behavior | Synthesis timing closure or board signal integrity |
| Physical interface or timing | Identified device and authorized instrument/fixture | Other board revisions, operating conditions, or tolerances |

Record the relevant source revision, built artifact, target identity, tool
versions, configuration, inputs, initial state, expected observations, and
cleanup. Existing logs and test-result formats suffice. A successful build,
flash command, transport handshake, or test discovery is not a passed behavior
check. Record unavailable and unexecuted layers distinctly.

## Define and exercise the contract

1. Obtain signal polarity, reset timing, clock domains, permitted ranges, units,
   tolerances, protocol timing, and expected failure behavior from the project's
   requirements or actual component interface. Do not invent limits from a
   convenient sleep or a familiar board. An unresolved external choice remains
   unresolved; routine test setup follows inspected project configuration.
1. Arrange the required state and apply the specific stimulus. Observe outputs
   after the relevant scheduling or settling condition, not before nonblocking
   assignments take effect. Include forbidden effects and reset/disable/error
   cases required by the contract. Treat unknown/high-impedance signal values
   explicitly; do not coerce them to a convenient zero.
1. Keep the oracle independent from the implementation. A testbench must not
   recompute the same private state machine line by line. Derive expected traces
   from the protocol/behavior and use a different compliant implementation where
   practical. A waveform screenshot alone is not a checked assertion.
1. Make termination meaningful. Detect a dead testbench, missing expected
   completion, or canceled assertion task rather than treating process exit as
   success. In cocotb, logging an error is not an assertion; inspect scheduled
   tasks and runner results. Do not accept a canceled task that never performed
   its assertions as verified behavior.
1. For test-first development, run the next behavioral test before its change,
   observe the relevant failure, implement, and rerun. A synthesis error or
   missing programmer cannot substitute for the behavioral failure being fixed.
   Keep implementation prose separate from executable evidence.

## Device authority and restoration

Flashing, fuses, voltage/current changes, destructive memory tests, relays, or
actuator motion require the relevant target and consequence to be authorized.
Inspect actual fixture limits before energizing anything. Never guess wiring,
probe addresses, credentials, or board selectors. Isolate persistent data and
restore only the state the test owns. If equipment is absent, run valid narrower
checks without labeling them a physical-device pass.

Use the established native runner's device/fixture selection and build-versus-
execution controls. For Zephyr projects, inspect that revision's Twister help
and test configuration; an ordinary build-only result does not demonstrate a
board run. For cocotb projects, retain the selected simulator, parameters, and
runner configuration. These are conditional examples, not dependencies to add to
unrelated projects.

## Executable HDL example

The [counter testbench](../assets/hdl-counter/counter_tb.sv) specifies a 4-bit
counter: synchronous reset has priority; enable increments until 15; disabled
cycles preserve value; increment at 15 saturates. This bounded fixture's values
are its explicit contract, not universal hardware limits.

The [implementation](../assets/hdl-counter/counter.sv) and
[alternative](../assets/hdl-counter/counter_equivalent.sv) must pass the same
port-level checks. A [wrapping fault](../assets/hdl-counter/counter_faulty.sv)
must fail on saturation, not syntax or simulator startup.

```sh
sh assets/hdl-counter/verify.sh
python3 assets/rename-contract/test_rename_operation.py
```

Run these from the skill root. The HDL runner requires provisioned Icarus
Verilog (`iverilog` and `vvp`), uses a disposable build directory, and refuses
an unexpected fault outcome. It performs simulation only; it does not
synthesize, flash, or test a physical device. The separate filesystem example
proves file movement under its stated no-concurrent-writer contract, not a
race-free no-clobber operation on arbitrary filesystems.

Sources: [cocotb testbenches][cocotb], [Zephyr Twister][twister]. Match the
project's selected versions before using particular CLI flags or APIs.

[cocotb]: https://docs.cocotb.org/en/v2.0.1/writing_testbenches.html
[twister]: https://docs.zephyrproject.org/latest/develop/test/twister.html
