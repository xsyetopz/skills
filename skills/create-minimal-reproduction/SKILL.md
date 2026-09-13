---
name: create-minimal-reproduction
description: >-
  Reduce a bug, regression, or API behavior to an independently executable
  minimal reproduction. Not for tutorials or production starters.
---

# Create Minimal Reproduction

A minimal reproduction is complete only when its documented command produced the
claimed observable result. Capture the original failure before reducing it:
exact command, expected and actual result, relevant diagnostic, versions,
OS/architecture, inputs, configuration, and state assumptions.

Work in a disposable directory. Start with the smallest artifact the ecosystem
actually needs: a source file and compiler command when sufficient; otherwise a
small project with its required manifest and configuration. Do not scaffold an
application, retain private source, or add a dependency that does not affect
the behavior.

Define a check for the observed failure (the oracle). Remove one independent
element at a time and re-run that check. Keep a removal only if the target
behavior remains. For races or flakes, preserve the
trigger, record sample count and failures, and state the observed rate; do not
claim deterministic reproduction when it is not deterministic.

Choose reductions from the failure's input classes, boundary values, interacting
conditions, and state sequence. A failure only on the second invocation needs
that history even if a one-call example is shorter. Keep the oracle independent
of the suspected implementation: match the intended diagnostic or effect, not
any nonzero exit. Re-check the original and reduced case under equivalent
conditions when a reduction could have changed the cause. Call a result reduced,
not globally smallest, unless that stronger claim has evidence.

Package every required file as text with exact setup and run commands, tested
environment, input/fixture, expected behavior, actual behavior, and exact
output when relevant. Re-run the documented instructions from a clean copy or
fresh state when caches, generated files, or environment state could affect the
result. If execution is blocked, report the blocker and call the result an
unverified candidate, not a verified reproduction.

For a small packaging example, inspect the bundled
[verified reproduction](assets/python-delimiter-repro/README.md). To exercise
that example, copy its directory to a clean location and run `python3 verify.py`
there; this is not required when reducing a different failure.

Read [reduction and packaging](references/reduction-and-packaging.md) when
choosing ecosystem-specific files or preparing a standalone upstream report.
