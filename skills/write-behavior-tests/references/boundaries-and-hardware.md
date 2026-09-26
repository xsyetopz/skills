# Packages, hosts, and hardware

Claims that a source-tree test cannot establish: the shipped artifact
works, the host application loads the extension, the logic works in
simulation, the device behaves. Each card says which layer it proves
and which it does not.

## Contents

- Installed package test
- Host-dependent behavior
- HDL testbench with a faulty alternative
- Evidence layers for firmware and devices

## Installed package test

**Definition.** Build the artifact with the project's release command,
install it into a clean environment, and run the tests from outside the
checkout, so local imports and files cannot hide anything missing from
the artifact ([src layout discussion][src-layout]).

**Use when.**

- A change touches packaging: data files, entry points, the `exports`
  map, build configuration.
- Users run the package, not the source tree.

**Do not use when.** The project ships no artifact, such as an internal
script run from the repository.

**Example.** [`assets/examples/package/`][package] reads
`greetings.json` with `importlib.resources`. Its test is
`tests/check_greet.py`, named so that the repository's `test_*.py`
runner does not import it from the checkout. `verify.sh network` runs
these steps in a temporary copy, with setuptools 80.9.0 pinned in
`pyproject.toml`:

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -p 'check_*.py'
uv build --wheel -o "$WORK/dist" .
uv venv "$WORK/venv"
uv pip install --python "$WORK/venv/bin/python" "$WORK"/dist/*.whl
cd "$WORK" &&
  "$WORK/venv/bin/python" -m unittest discover -s "$WORK/package/tests" \
  -p 'check_*.py'
# FileNotFoundError: .../site-packages/greet/greetings.json
```

The data file is in the checkout but missing from the wheel, because
setuptools' `include_package_data` picks up only files listed in
`MANIFEST.in` or reported by a VCS plugin ([setuptools data
files][datafiles]). The fix, in `pyproject.fixed.toml`:

```toml
[tool.setuptools.package-data]
greet = ["*.json"]
```

After the fix, the wheel lists `greet/greetings.json` and the installed
test passes.

**Cost removed.** Releases that break on install. Only the installed
test detects this failure; the checkout test cannot.

**Verify.**

1. `unzip -l dist/*.whl` (or `npm pack --dry-run`, or `cargo package
   --list`) shows every runtime file.
1. The installed test runs from a directory that contains no source
   tree.

## Host-dependent behavior

**Definition.** Some behavior exists only inside a host application:
editor extension activation, contribution points, permission prompts,
UI commands, plugin unloading. Pure-logic tests cannot see it. A host
test runs the real host, headless where possible.

**Use when.** The change affects how the host loads or calls the code:
the manifest, activation, registration, packaging, unloading.

**Do not use when.** The change is pure logic behind a stable
interface. A unit test is enough, and the host test stays unchanged.

**Example.** The editor skills hold the host commands:
`$develop-vscode-extensions` (`@vscode/test-electron`),
`$develop-intellij-platform-plugins` (`BasePlatformTestCase`),
`$develop-neovim-plugins` (`nvim --headless`),
`$develop-zed-editor-extensions`, `$develop-sublime-text-plugins`, and
`$develop-eclipse-ide-plugins`.
For example, `$develop-neovim-plugins` runs its example plug-in's host
test from the plug-in root:

```sh
nvim --clean --headless -u tests/minimal_init.lua -l tests/run.lua
```

Not runnable here: `nvim` is not installed on this machine.

**Cost removed.** An extension that passes its unit tests but never
activates, because of a wrong activation event or a missing
contribution.

**Verify.**

1. The report lists which claims were checked in the real host.
1. If the host could not run, the report marks those claims
   "Not runnable here" with the error, not as passed.

## HDL testbench with a faulty alternative

**Definition.** A testbench drives the design's ports and clock and
checks the outputs against the stated contract after the relevant
clock edge. It runs against the design, a conforming alternative, and a
deliberately faulty version. The harness also detects a testbench that
never finishes its checks.

**Use when.** RTL changes: counters, state machines, protocol logic.

**Do not use when.** The claim concerns timing closure, synthesis
results, or signal integrity on a board. Simulation does not establish
those.

**Example.** [`hdl-counter/`][hdl] specifies a 4-bit counter:

- synchronous reset takes priority;
- enable increments;
- the count saturates at 15.

The testbench prints `CONTRACT PASS` only after every check.

```systemverilog
task automatic cycle(input bit rst, en, input logic [3:0] expected);
  @(negedge clk);
  reset = rst;
  enable = en;
  @(posedge clk);
  #1; // Observe after this fixture's nonblocking assignments.
  if (count !== expected) begin
    $display("CONTRACT FAIL: expected=%0d observed=%0d", expected, count);
    $fatal(1, "counter output violates the stated contract");
  end
endtask
```

`hdl-counter/verify.sh` requires `counter.sv` and
`counter_equivalent.sv` to print `CONTRACT PASS`, and
`counter_faulty.sv`, which wraps to 0, to fail with exactly
`CONTRACT FAIL: expected=15 observed=0`.

Verification tier: not runnable here. Icarus Verilog (`iverilog`,
`vvp`) is not installed on this machine, so `verify.sh` prints
`SKIP hdl card`. The script refuses to report success when the fault
fails for any other reason.

**Cost removed.** Wrap-around bugs found on hardware instead of in
simulation, and tests that "pass" only because the simulation stopped
early.

**Verify.**

1. `sh hdl-counter/verify.sh` exits 0: both conforming designs pass,
   and the fault fails with the exact expected message.
1. The report says "simulation" and does not claim synthesis or device
   behavior.

## Evidence layers for firmware and devices

**Definition.** Name the layer that produced each piece of evidence:

- host unit test;
- instruction or peripheral simulator;
- HDL simulation;
- hardware-in-the-loop with an identified board;
- physical measurement with an instrument.

A build, a flash command, or test discovery is not a behavior check.

**Use when.** Firmware, embedded, or hardware claims.

**Do not use when.** Using it to justify touching a device without
authorization. Flashing, fuses, voltage changes, and actuator motion
need explicit approval and known fixture limits.

**Example.**

| Claim | Layer that ran | Not established |
| --- | --- | --- |
| Parser rejects bad frame | host unit test | interrupt timing |
| Counter saturates | HDL simulation (when iverilog present) | synthesis timing |
| UART at 115200 baud | not run: no board attached | everything physical |

The HDL row comes from this step in `assets/examples/verify.sh`, which
names the layer and says when it did not run:

```sh
# 6. HDL: simulation only, when Icarus Verilog is installed.
if command -v iverilog >/dev/null 2>&1 && command -v vvp >/dev/null 2>&1; then
    sh "$WORK/hdl-counter/verify.sh" >hdl.log 2>&1 || fail "hdl: $(cat hdl.log)"
    ok "hdl: counter and equivalent pass, wrapping fault rejected"
else
    echo "SKIP hdl card: iverilog/vvp not installed (simulation not run)"
fi
```

Locally, `sh verify.sh` printed the `SKIP hdl card` line, so that
row's evidence is "not run" here.

For Zephyr, `twister` without a board runs only build or emulation;
check the revision's `twister --help` before using its flags
([Twister][twister]). In cocotb, a logged error is not an assertion
failure, so check the runner's result ([cocotb][cocotb]).

**Cost removed.** "Tested on hardware" claims that were only a build.
The table makes the gap visible.

**Verify.**

1. Every claim in the report has a layer; claims without one are
   listed as open.
1. Device runs record the board identity, firmware revision, tool
   versions, and the restore steps.

[src-layout]: https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/
[datafiles]: https://setuptools.pypa.io/en/latest/userguide/datafiles.html
[package]: ../assets/examples/package/
[hdl]: ../assets/examples/hdl-counter/counter_tb.sv
[twister]: https://docs.zephyrproject.org/latest/develop/test/twister.html
[cocotb]: https://docs.cocotb.org/en/v2.0.1/writing_testbenches.html
