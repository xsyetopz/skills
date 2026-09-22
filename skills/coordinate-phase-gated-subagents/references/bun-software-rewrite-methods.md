# Adapt subagent methods from Bun's software rewrite

Primary source: <https://bun.com/blog/bun-in-rust> (Jarred Sumner, July 8,
2026).

This skill adapts engineering mechanisms from Bun's large Zig-to-Rust rewrite;
it does not copy its lifecycle. Bun used many continuously running dynamic
workflows. Here those mechanisms operate **inside sequential software
development phases**.

## Practices retained

- **Preparation before production code.** Bun first built shared
  source-to-target software translation and lifetime guidance before attempting
  the full translation. For the Waterfall software development model, these
  become requirements/design baseline inputs.
- **Trial before scale.** Bun ported a few files before scaling to the full
  corpus. Here a trial is a design-feasibility proof and orchestration check;
  production rollout still waits for the design phase completion check.
- **Role separation.** Bun used one implementer, two or more adversarial
  reviewers, then a correction-and-integration agent. Reviewers had separate
  context and were tasked to find faults rather than justify the implementation.
- **Parallel software-work assignment.** Work was partitioned across multiple
  workflows and worktrees once collision problems were discovered.
- **Compiler/test failures as work queues.** Error output was captured, grouped,
  assigned, reviewed, fixed, and integrated rather than handled as one enormous
  conversational task.
- **Process correction over repeated hand patches.** When agents repeatedly
  stubbed functions or produced bad workarounds, the workflow instructions were
  changed so subsequent workers stopped generating the same defect class.
- **Independent verification.** Compilation alone was insufficient; executable
  commands, subcommands, the existing test suite, sanitizers, and behavior
  checks were progressively brought online.

## Practices deliberately changed for sequential software development

- No continuous lifecycle loop across requirements, design, and implementation.
- No production implementation before requirements and design are baselined.
- A late defect in a frozen upstream artifact creates a formal change request;
  it does not silently mutate the baseline.
- Parallelism is permitted only among work items whose ownership and dependency
  constraints allow it.

## Important caution

The Bun article demonstrates one unusually large software rewrite under a
specific team, codebase, model, compute budget, and test suite. Its throughput
numbers are not portable performance targets. Reuse the controls, not the
claimed scale.
