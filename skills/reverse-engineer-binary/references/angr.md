# angr

Facts read on 2026-10-05. PyPI had angr 10.0.1.post1 (2026-10-02), which needs Python 3.10+. The
`angr-doc` repository is stale (last pushed 2023), so read the `docs/*.rst` files in the angr
repository instead.

## Setup

Install with `pip install angr` inside an isolated environment (a virtualenv or `uv` tool
environment), not into the system Python.

## Loading

From `docs/core-concepts/loading.rst`:

- `auto_load_libs` is off by default. When on, real library code runs and "will most likely cause an
  explosion of the number of states". Leave it off.
- With it off, externals are stubbed by SimProcedures, or by `ReturnUnconstrained`, which returns a
  unique unconstrained symbolic value. `use_sim_procedures=True` is the default.
- Related options: `except_missing_libs`, `force_load_libs`, `skip_libs`.

## Exploring

From `docs/core-concepts/pathgroups.rst`:

- `simgr.explore(find=addr|list|func, avoid=..., num_find=1)`. Results land in `simgr.found`.
- Pattern: `find=lambda s: b"Congrats" in s.posix.dumps(1)`, then `simgr.found[0].posix.dumps(0)`
  gives the input that reached it.
- Exploration techniques include DFS, Explorer, LengthLimiter, LoopSeer, ManualMergepoint, and
  MemoryWatcher.
- The FAQ warns about state explosion and slowness. Bound a run with a state or step limit, a
  timeout, and `avoid` addresses, and report a run that hits a bound as inconclusive, not as "no
  path".

## CFG

From `docs/analyses/cfg.rst`: `p.analyses.CFGFast()` (options `function_starts`, `normalize`,
`resolve_indirect_jumps`) and `CFGEmulated(keep_state=True)`. CFGFast results are a recovery
heuristic, so confirm an edge in the disassembly before quoting it.

## Unverified

- The exact `angr.Project(...)`, `factory.entry_state()`, and `simulation_manager` signatures were
  not read from source. Check them against the installed version before writing a script.

## Sources

- angr/angr: <https://github.com/angr/angr>
- angr loading.rst: <https://github.com/angr/angr/blob/master/docs/core-concepts/loading.rst>
- angr pathgroups.rst: <https://github.com/angr/angr/blob/master/docs/core-concepts/pathgroups.rst>
- angr cfg.rst: <https://github.com/angr/angr/blob/master/docs/analyses/cfg.rst>
