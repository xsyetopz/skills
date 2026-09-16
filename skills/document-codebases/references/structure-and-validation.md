# Organize and verify software repository documentation

Version-sensitive reference; select the actual target version. Use the
repository's existing documentation toolchain and publication target. A Markdown
edit does not justify a new static-site generator, a custom documentation
schema, or installation of a competing formatter.

## Match the reader's task

[Diátaxis](https://diataxis.fr/) distinguishes learning tutorials, task-oriented
how-to guides, factual reference, and explanations. Use those distinctions to
remove mixed-purpose detours, not to require four directories in a small repo.
Keep a quickstart focused on a supported first result. Put exhaustive options in
reference and design trade-offs in explanation; link between them.

For an API reference, find the authoritative interface and existing generator:
source declarations, protocol specification, or a checked-in API description.
Change its input and regenerate with the established command. Do not hand-edit
generated reference or invent an OpenAPI document for a non-HTTP interface.
Preserve version-specific contracts and distinguish release docs from mainline.

Record an architecture decision only when there is an actual decision to retain.
Use the existing ADR convention; otherwise concise context, decision,
alternatives, and consequences are sufficient. Do not manufacture approval,
status history, numbering rules, or a versioned ADR schema. Label proposed
choices separately from accepted decisions, and preserve superseded rationale
when it explains migration.

## Verify procedures as a reader

Run changed examples from their stated directory with the stated prerequisites.
Use an isolated checkout or temporary output directory when the command modifies
files. Do not run destructive deployment or publication examples merely to
validate prose. Verify those against the actual command contract and report the
unexecuted boundary.

Check successful output and a relevant failure path, not only command exit
status. For a CLI, confirm option names using its actual parser/help, input
encoding, stdin/file behavior, output location, and overwrite behavior where
applicable. Do not replace an unsupported documented flag by changing the
application unless runtime work was requested. Fix the documentation to the
supported interface.

A shell snippet containing an expected output transcript is not directly
executable as a whole. Separate commands from output. Use fake credentials,
non-production endpoints, and user-controlled paths; never include real secrets.
Prefer the repository's doctest, executable-example, or smoke-test tooling. A
Markdown parser/linter proves syntax or style, not that instructions work.

## Links, rendering, and accessibility

Resolve local links relative to the document, including images and fragments.
Check public links against the intended release/version. A successful HTTP
status can still be a login page or redirect to unrelated navigation; inspect
the target content. Do not claim private/offline destinations are valid without
access.

GitHub's [README rendering rules][readme] support relative links and generated
heading anchors. Moving a file can change both routes; update its callers and
verify the rendered destination rather than guessing every anchor conversion.
Use descriptive link text, useful image alternatives, and logical headings. Do
not communicate a required distinction by color or a diagram alone.

Prefer Mermaid to hand-drawn ASCII when a diagram improves understanding. GitHub
supports fenced `mermaid` blocks, but its renderer version controls syntax
support; verify compatibility rather than relying on a newer local renderer.
Provide a short textual explanation of the important relationship. Follow
[GitHub's diagram documentation][diagrams] for the actual target.

Report separately: commands executed and their observed results, generated docs
rebuilt, links checked, rendering inspected, and checks not performed. Preserve
existing lint, type-check, and test requirements; do not lower them to accept
documentation examples.

[readme]:
https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes
[diagrams]:
https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/creating-diagrams
