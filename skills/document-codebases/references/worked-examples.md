# Worked documentation examples

## Complete CLI example

```text
Repository root: /path/to/project
Prerequisite: tool version from .tool-versions
Command: just validate
Expected: project-defined validators run; exit 0 means those checks passed
Does not prove: production deployment or unavailable platform tests
```

A useful guide names the working directory and interpretation. It does not paste
an invented “Success!” transcript.

## GitHub-supported workflow diagram

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant Config
    participant Service
    User->>CLI: project deploy --env staging
    CLI->>Config: load declared target
    CLI->>Service: submit artifact digest
    Service-->>CLI: deployment ID and status
    CLI-->>User: exact result or error
```

The prose must still explain authentication, artifact identity, failure states,
and cleanup. The diagram is navigation, not the whole contract.

## Formatting-only boundary

When asked to normalize Markdown tables, do not replace `npm ci` with `bun
install`, modernize APIs, rename headings, or rewrite supported versions. Those
are substantive changes requiring separate evidence and authority.
