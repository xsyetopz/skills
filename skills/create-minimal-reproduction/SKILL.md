---
name: create-minimal-reproduction
description: >-
  Reduce a bug, regression, or API behavior to an independently executable
  minimal reproduction. Not for tutorials or production starters.
---

# Create Minimal Reproduction

An MRE is complete only when its documented command was run and produced the
claimed observable result. Capture the original failure before reducing it:
exact command, expected and actual result, relevant diagnostic, versions,
OS/architecture, inputs, configuration, and state assumptions.

Work in a disposable directory. Start with the smallest artifact the ecosystem
actually needs: a source file and compiler command when sufficient; otherwise a
small project with its required manifest and configuration. DO NOT scaffold an
application, retain private source, or add a dependency that does not affect
the behavior.

Remove one independent element at a time and re-run the same oracle. Keep a
removal only if the target behavior remains. For races or flakes, preserve the
trigger, record sample count and failures, and state the observed rate; do not
claim deterministic reproduction when it is not deterministic.

Package every required file as text with exact setup and run commands, tested
environment, input/fixture, expected behavior, actual behavior, and exact
output when relevant. Re-run the documented instructions from a clean copy or
fresh state when caches, generated files, or environment state could affect the
result. If execution is blocked, report the blocker and call the result an
unverified candidate, not an MRE.

## Unverified fragment

**Deciding condition:** An upstream maintainer must reproduce the failure
without access to the original repository.

```text
The client sometimes crashes.

src/client.ts: client.fetchData()
```

Why it fails:

- No dependency versions, input, command, or exact diagnostic are supplied.
- Another person cannot execute the claimed failure.

## Independently executable artifact

```text
python-delimiter-repro/
├── README.md
├── repro.py
└── verify.py
```

Why it works:

- The artifact contains the files and command needed to observe the condition.
- The report states the tested environment and observable difference.

Check: copy the bundled [verified example](assets/python-delimiter-repro/) to a
clean location and run `python3 verify.py` from it.

Read [reduction and packaging](references/reduction-and-packaging.md) for the
reduction log, report shape, ecosystem fit, and upstream-reporting details.
