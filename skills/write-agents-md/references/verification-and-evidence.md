# Verification and evidence

Select evidence at the boundary of the claim. Run the smallest sufficient set
first, then broaden only when the change crosses another contract boundary.

| Claim | Sufficient evidence | Not sufficient by itself |
| --- | --- | --- |
| Command is correct | Repository config/source and executed or provider-validated command in stated directory. | README copied without verification. |
| Scope applies | File-tree/client precedence inspection and representative loading check. | Filename location guessed. |
| Generated file rule is valid | Generator/source relationship and successful regeneration/clean diff. | Header comment alone. |
| Instruction is needed | Observed recurring failure or non-obvious invariant not sufficiently enforced elsewhere. | General best practice. |
| No conflict remains | All applicable instruction layers reviewed for the target path. | Root file alone inspected. |

## Command patterns

Use the repository’s existing commands. Record the exact command, working
directory, revision, configuration, and result.

## Result reporting

Separate authored checks, executed checks, static analysis, simulation,
integration/host execution, production observations, skipped checks, and
unavailable checks. Include relevant failure output. A green check establishes
only the properties it can discriminate; a single flaky pass, successful parser,
or valid configuration file is not broad runtime proof.
