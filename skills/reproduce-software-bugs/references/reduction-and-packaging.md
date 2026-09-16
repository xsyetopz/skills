# Reduce and package a software failure reproduction

Stack Overflow defines an MRE as minimal, complete, and reproducible, and
recommends testing the example before sharing it. See [its MRE guidance][mre].

## Oracle and reduction log

Write one observable failure check before editing: an exit status, assertion,
exact diagnostic, output value, HTTP response, or a measured failure rate. A
build failure is a valid failure check only when that failure is the reported
behavior.

For each removal, record the element removed, the command run, and whether the
same failure remains. Candidates include files, configuration properties,
dependencies, input portions, and options. Keep this log with the working case;
the final artifact needs only the files and instructions that reproduce it.

Do not minimize character count at the expense of readable names, formatting, or
the trigger. Do not replace a race with a sequential failure and call it the
same reproducer.

## Choose the artifact shape

- Use one source file and an exact compiler or interpreter command when that is
  enough.
- Include the smallest manifest, lockfile, and configuration only when they
  affect resolution, build, runtime, or the reported behavior.
- Include both sides of an integration, fixtures, and environment setup when
  they are necessary. A prose reconstruction is not a complete artifact.
- Omit credentials and private data. Replace them with minimal synthetic values
  that preserve the condition.

Use the ecosystem's smallest executable shape:

- C or C++: one source file plus the exact compiler command, unless flags,
  generated inputs, or linking require a build file.
- Rust: `Cargo.toml` plus the smallest source tree when Cargo resolution or
  features matter; otherwise use the exact `rustc` command.
- .NET: one project file and source file with the exact `dotnet` command.
- JVM: a source/compiler command when sufficient, or the smallest supported
  Gradle or Maven project when build behavior matters.
- JavaScript, TypeScript, or Bun: omit a manifest when one runtime command is
  sufficient; include it and the lockfile when dependencies or resolution are
  part of the behavior.
- Browser: runnable HTML, CSS, and JavaScript with browser/version details.
- HTTP, database, or plug-in integration: include both required sides, minimal
  fixture/state setup, and the actual host or engine when its semantics are the
  claim.

Do not replace an ecosystem-native mini-project with disconnected snippets that
cannot build or run together.

## Delivery record

Place this information in the artifact's `README.md` or issue body:

```text
Title: <specific unexpected behavior>

Prerequisites: <tool/runtime and version>
Tested environment: <OS, architecture, relevant versions>
Files: <all included source, manifest, config, fixture files>
Setup: <exact command>
Run: <exact command>
Input/state: <fixture, seed, service setup, cache/state assumptions>
Expected: <specific observable result>
Actual: <specific output or diagnostic>
Verification: <command run, date/context, exit status or observed sample>
Nondeterminism: <trials, failures, rate; omit when deterministic>
```

For an upstream report, make the artifact stand alone: do not require access to
the original repository, secret infrastructure, or omitted configuration. Keep
the original failure details separately if they contain sensitive data.

[mre]: https://stackoverflow.com/help/minimal-reproducible-example

## Delimiter reproduction

Use [the complete Python reproduction][the-complete-python-reproduction] when
constructing or testing a delimiter-parsing report. Copy the directory; run the
commands below from that copy. For a shareable output, put these run
instructions in the requested report or issue rather than adding a second skill
entrypoint.

This artifact reproduces a parser failure when a text field contains the
protocol delimiter.

### Prerequisites

- Python 3.10 or newer

Reproduced during this rebuild with CPython 3.13.5 on Linux x86-64.

### Run

Run `python3 repro.py` from this directory.

Input: `42|start|stop`

Expected: parse message ID `42` and text `start|stop`.

Actual on the tested environment: the process exits nonzero with `ValueError:
too many values to unpack (expected 2)`. Exact suffixes can vary with Python
versions; the verifier requires the relevant exception prefix.

### Verify

Run `python3 verify.py`. The verifier exits zero only when `repro.py` produces
the documented `ValueError` failure.

[the-complete-python-reproduction]: ../assets/python-delimiter-repro
