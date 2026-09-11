# README and contribution workflow

Lead a README with what the project does and one representative result. Follow
with supported prerequisites, installation from a stated directory, the smallest
useful command, expected output location, and links to deeper
configuration/troubleshooting. Derive package names and flags from the
executable/manifests. Separate contributor builds from end-user installation; a
source checkout may require tools that a release binary does not.

State the working directory, exact command, required environment, and expected
output for each procedure. Verify package names, flags, and output paths against
the implementation. Limit platform claims to supported targets.

Write CONTRIBUTING around the supported change path: setup, focused/full checks,
code generation, how to submit a useful issue/PR, and existing review
conventions. Link existing security reporting and licensing policy; do not
create signing, DCO/CLA, conduct or disclosure requirements without authority.
Give an actionable fix for each prerequisite failure.
