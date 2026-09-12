# Reduction and packaging

Stack Overflow defines an MRE as minimal, complete, and reproducible, and
recommends testing the example before sharing it. See [its MRE guidance][mre].

## Oracle and reduction log

Write one observable oracle before editing: an exit status, assertion, exact
diagnostic, output value, HTTP response, or a measured failure rate. A build
failure is a valid oracle only when that failure is the reported behavior.

For each removal, record the element removed and whether the same oracle still
holds. Use this loop:

1. Copy the failing case to a disposable directory.
1. Remove one independent source file, configuration property, dependency,
   input portion, option, or feature.
1. Run the documented command.
1. Keep the removal only when the relevant oracle remains true.
1. Repeat; use a clean run when caches or state are plausible causes.

Do not minimize character count at the expense of readable names, formatting, or
the trigger. Do not replace a race with a sequential failure and call it the
same reproducer.

## Choose the artifact shape

- Use one source file and an exact compiler or interpreter command when that
  is enough.
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
