# Verification and claim evidence for Repository Agent Instructions

Select evidence that can discriminate the claimed property of the AGENTS.md
instructions. Run the smallest sufficient check first. Broaden only when another
contract boundary changed.

| Claim | Sufficient evidence | Not sufficient by itself |
| --- | --- | --- |
| Command is correct | Repository config/source and executed or provider-validated command in stated directory. | README copied without verification. |
| Scope applies | File-tree/client precedence inspection and representative loading check. | Filename location guessed. |
| Generated file rule is valid | Generator/source relationship and successful regeneration/clean diff. | Header comment alone. |
| Instruction is needed | Observed recurring failure or non-obvious invariant not sufficiently enforced elsewhere. | General best practice. |
| No conflict remains | All applicable instruction layers reviewed for the target path. | Root file alone inspected. |

## Command patterns

Use the repository's existing commands. Record the exact command, working
directory, revision, configuration, and result.

## Result reporting

For the AGENTS.md instructions, separate authored checks, executed checks,
static analysis, simulation, host/integration execution, production
observations, skips, and unavailable checks. Include useful failure output. A
green check establishes only the property that it can discriminate.
