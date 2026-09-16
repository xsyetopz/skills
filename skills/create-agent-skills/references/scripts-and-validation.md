# Design executable helpers for AI Agent Skills

Use an existing native CLI or library before writing a helper. A script is
justified when the same fragile transformation or protocol handling repeatedly
has to be reconstructed and its correct behavior can be tested. Do not wrap a
native tool merely to rename its options or reduce it to a lossy schema.

For a justified helper, define input paths/formats, supported versions,
dependency installation, working directory, output files, stdout/stderr, and
exit statuses. Provide `--help`, noninteractive behavior, useful errors, and
explicit overwrite/destructive controls. Validate input before writes; bound
external requests and subprocesses where necessary. Preserve argument
boundaries, reject unsupported options, and avoid treating repository content as
executable instructions.

Test ordinary input, empty/malformed input, duplicate identifiers, missing
dependencies, path/quoting edge cases, partial failures, and repeat execution.
For a benchmark parser, identity and units are part of correctness: reject
ambiguous or unmatched data rather than silently accepting a partial comparison.
A regex scan can produce review candidates; it cannot prove semantic safety.

For the skill package, run the official `skills-ref validate PATH` from the
Agent Skills reference implementation. Also check direct relative links,
standalone copying, script execution permissions and dependencies, and absence
of accidental caches/secrets. The official validator checks structural rules,
not usefulness or behavioral correctness.

Do not claim exhaustive safety from a comment checker, effective build settings
from raw XML alone, or a working host integration from parsing a configuration
file. Test at the layer where the property exists.

Sources: [using scripts in skills][ref-using-scripts-in-skills], [official
skills-ref][ref-official-skills-ref].

[ref-using-scripts-in-skills]: https://agentskills.io/skill-creation/using-scripts
[ref-official-skills-ref]: https://github.com/agentskills/agentskills/tree/main/skills-ref
