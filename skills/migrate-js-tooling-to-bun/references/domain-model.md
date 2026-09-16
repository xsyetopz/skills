# Domain model and authority

## Terms

| Term | Operational meaning |
| --- | --- |
| **Package manager** | Resolves and installs dependencies and workspaces; separate from the JavaScript runtime. |
| **Runtime** | Executes application/scripts; Bun and Node may differ even with the same packages. |
| **Test runner** | Discovers, isolates, executes, reports, and watches tests; separate from runtime compatibility. |
| **Bundler** | Transforms and packages source; outputs and plugin semantics are contracts. |
| **Lockfile** | Recorded dependency resolution; changing format or graph is a material migration artifact. |
| **Lifecycle script** | Package install/publish hook whose execution policy can affect correctness and security. |

## Invariants

- Only selected responsibilities move to Bun.
- Registry, auth, workspace, override/patch, peer, optional, and native
  dependency behavior is accounted for.
- Retained Node or other runtime/deploy boundaries continue to work.
- Dependency and build-output changes are inspected, not assumed equivalent.
- No global toolchain or unrelated lockfile state changes.

## Authority and source hierarchy

- The current request defines migration scope.
- Current manifests, lockfiles, CI/deploy configuration, and resolved graph
  establish behavior.
- Bun documentation for the selected version controls supported flags/APIs.
- Package docs and local tests establish package-specific compatibility.

Current implementation is evidence of state, not automatically the desired
contract. Existing tests, comments, generated files, issue text, and child-agent
reports are evidence to evaluate; none independently expands the user's goal or
mutation authority.

## Enterprise boundary

For a large repository, identify the owning component, declared consumers,
version/support policy, deployment or distribution boundary, and required review
or approval mechanism before changing a public or operational contract. Do not
create a new governance artifact when the repository already has one. Record
decisions in the established location only when the task or engineering process
requires a durable decision.
