"""Measure how reliably catalog skill descriptions trigger in Claude Code.

Follows the agentskills.io "Optimizing skill descriptions" method. Each
selected skill's `evals/eval_queries.json` is a list of
`{"query", "should_trigger", "split": "train"|"validation", "expected_skill"?}`.
The whole catalog is installed in an isolated project for every run, so each
skill competes with every other catalog skill. A run reads past meta tools
(ToolSearch, TodoWrite, TaskCreate/TaskUpdate/TaskList/TaskGet) and is stopped
at the first other tool call: a `Skill` call names the skill that fired, any
other tool (or none) means no skill fired. The tool names up to that call are
recorded as `tool_prefix`. A query passes when its trigger rate is above the
threshold for should-trigger queries, or below it for should-not-trigger
queries; a rate exactly at the threshold fails both.

Each concurrent job owns a fixed project directory under the system temp dir
(skill-evals-trigger/slot-<n>), recreated with identical content before every
run, so the system prompt (which includes the working directory) is reused
from the prompt cache across runs. Two harness processes wait for each
other's slots rather than share them.

`expected_skill` (optional) names the skill that should fire instead; its rate
is reported but does not change pass/fail.

Examples:
  just eval-triggers --skill optimize-go-code --dry-run
  just eval-triggers --skill optimize-go-code --split train --runs 3 --jobs 4
  just eval-triggers --skill write-justfiles --model claude-fable-5-1 --effort medium --json
  python3 scripts/evals/trigger_eval.py --catalog /tmp/candidate-skills --skill optimize-go-code

Output: <out>/triggers-<UTC timestamp>/ holds settings.json, isolation.json,
the catalog snapshot, one stream per run under streams/, and results.json.
Without --json, stdout gets one line per query; with --json, the summary JSON.
Diagnostics go to stderr.

Exit codes:
  0  every query passed
  1  at least one query failed its threshold
  2  usage error or invalid eval_queries.json
  3  isolation or model guard failure (preflight, collision, other model used)
  4  a run failed (timeout, crash, or no events)
"""

from __future__ import annotations

import argparse
import json
import queue
import shlex
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import harness

SPLITS = ("train", "validation")


@dataclass(frozen=True)
class Query:
    skill: str
    index: int
    query: str
    should_trigger: bool
    split: str
    expected_skill: str | None


def load_queries(skill: str, path: Path) -> list[Query]:
    try:
        data = harness.read_json(path)
    except (OSError, ValueError) as error:
        raise harness.UsageError(f"{path}: {error}") from error
    if not isinstance(data, list):
        raise harness.UsageError(f"{path}: expected a JSON list of queries")
    queries: list[Query] = []
    for index, item in enumerate(data):
        where = f"{path}[{index}]"
        if not isinstance(item, dict):
            raise harness.UsageError(f"{where}: expected an object")
        text = item.get("query")
        should = item.get("should_trigger")
        split = item.get("split")
        expected = item.get("expected_skill")
        if not isinstance(text, str) or not text.strip():
            raise harness.UsageError(f"{where}: 'query' must be a non-empty string")
        if not isinstance(should, bool):
            raise harness.UsageError(f"{where}: 'should_trigger' must be true or false")
        if split not in SPLITS:
            raise harness.UsageError(
                f"{where}: 'split' must be 'train' or 'validation'"
            )
        if expected is not None and not isinstance(expected, str):
            raise harness.UsageError(f"{where}: 'expected_skill' must be a string")
        queries.append(Query(skill, index, text, should, split, expected))
    return queries


def select_queries(queries: list[Query], split: str, limit: int | None) -> list[Query]:
    chosen = [q for q in queries if split == "all" or q.split == split]
    return chosen[:limit] if limit is not None else chosen


def rate(count: int, runs: int) -> float:
    return count / runs if runs else 0.0


def query_passed(should_trigger: bool, trigger_rate: float, threshold: float) -> bool:
    """Per the guide: above the threshold to pass a should-trigger query, below it otherwise."""
    return trigger_rate > threshold if should_trigger else trigger_rate < threshold


def score_query(
    query: Query, fired: list[str | None], threshold: float
) -> dict[str, Any]:
    """Aggregate one query's runs; `fired` is the skill each run invoked first, or None."""
    runs = len(fired)
    triggers = sum(1 for name in fired if name == query.skill)
    trigger_rate = rate(triggers, runs)
    others = Counter(name for name in fired if name and name != query.skill)
    scored: dict[str, Any] = {
        "skill": query.skill,
        "index": query.index,
        "query": query.query,
        "should_trigger": query.should_trigger,
        "split": query.split,
        "triggers": triggers,
        "runs": runs,
        "trigger_rate": round(trigger_rate, 4),
        "passed": query_passed(query.should_trigger, trigger_rate, threshold),
        "other_skills_fired": dict(sorted(others.items())),
    }
    if query.expected_skill:
        hits = sum(1 for name in fired if name == query.expected_skill)
        scored["expected_skill"] = query.expected_skill
        scored["expected_skill_rate"] = round(rate(hits, runs), 4)
    return scored


def summarize(scored: list[dict[str, Any]]) -> dict[str, Any]:
    def block(items: list[dict[str, Any]]) -> dict[str, Any]:
        passed = sum(1 for item in items if item["passed"])
        positives = [i for i in items if i["should_trigger"]]
        negatives = [i for i in items if not i["should_trigger"]]
        return {
            "queries": len(items),
            "passed": passed,
            "failed": len(items) - passed,
            "pass_rate": round(rate(passed, len(items)), 4) if items else None,
            "should_trigger_passed": sum(1 for i in positives if i["passed"]),
            "should_trigger_total": len(positives),
            "should_not_trigger_passed": sum(1 for i in negatives if i["passed"]),
            "should_not_trigger_total": len(negatives),
        }

    per_skill: dict[str, Any] = {}
    for skill in sorted({item["skill"] for item in scored}):
        items = [item for item in scored if item["skill"] == skill]
        per_skill[skill] = {
            "all": block(items),
            **{
                split: block([i for i in items if i["split"] == split])
                for split in SPLITS
            },
        }
    return {
        "overall": block(scored),
        "per_split": {
            split: block([i for i in scored if i["split"] == split]) for split in SPLITS
        },
        "per_skill": per_skill,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(__doc__ or "").partition("\n\n")[0],
        epilog=(__doc__ or "").partition("\n\n")[2],
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--skill",
        action="append",
        default=[],
        help="skill to evaluate (repeatable; default: every skill with eval_queries.json)",
    )
    parser.add_argument(
        "--split",
        choices=(*SPLITS, "all"),
        default="all",
        help="query split to run (default: all)",
    )
    parser.add_argument(
        "--runs", type=int, default=3, help="runs per query (default: 3)"
    )
    parser.add_argument(
        "--jobs", type=int, default=4, help="concurrent claude processes (default: 4)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="run at most this many queries in total, in file order",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.5,
        help="trigger-rate threshold (default: 0.5)",
    )
    parser.add_argument(
        "--model",
        default=harness.DEFAULT_MODEL,
        help=f"one of {', '.join(harness.ALLOWED_MODELS)}",
    )
    parser.add_argument(
        "--effort",
        default=harness.DEFAULT_EFFORT,
        help="low, medium, high (default), or xhigh; max is rejected",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=300,
        help="seconds before a run is stopped (default: 300)",
    )
    parser.add_argument(
        "--permission-mode",
        default="dontAsk",
        help="claude --permission-mode for runs (default: dontAsk, so no tool that needs approval runs before the stop)",
    )
    parser.add_argument(
        "--catalog",
        type=Path,
        default=harness.CATALOG_DIR,
        help="catalog directory holding <skill>/SKILL.md (default: skills/)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=harness.DEFAULT_OUT,
        help="output root (default: .evals/ at the repository root)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print the settings and commands; make no model calls",
    )
    parser.add_argument(
        "--json", action="store_true", help="print the summary JSON on stdout"
    )
    args = parser.parse_args(argv)
    if args.runs < 1 or args.jobs < 1 or (args.limit is not None and args.limit < 1):
        parser.error("--runs, --jobs, and --limit must be positive")
    if not 0 < args.threshold <= 1:
        parser.error("--threshold must be in (0, 1]")
    return args


def slot_queue(jobs: int) -> queue.Queue[int]:
    """Workspace slot numbers, one per concurrent run."""
    slots: queue.Queue[int] = queue.Queue()
    for slot in range(jobs):
        slots.put(slot)
    return slots


def log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def run_one(
    query: Query, attempt: int, catalog: dict[str, Path], ctx: dict[str, Any]
) -> dict[str, Any]:
    command = harness.claude_command(
        query.query,
        model=ctx["model"],
        effort=ctx["effort"],
        settings=ctx["settings_path"],
        permission_mode=ctx["permission_mode"],
    )
    slot = ctx["slots"].get()
    try:
        with harness.slot_project(ctx["slots_dir"], slot, catalog) as project:
            run = harness.run_claude(
                command, project, ctx["env"], ctx["timeout"], stop_at_decisive_tool=True
            )
    finally:
        ctx["slots"].put(slot)
    stream = ctx["streams"] / query.skill / f"q{query.index:03d}-run{attempt}.jsonl"
    stream.parent.mkdir(parents=True, exist_ok=True)
    stream.write_text("".join(run.lines), encoding="utf-8")
    events = run.events
    prefix, tool = harness.tool_prefix(events)
    init = harness.init_event(events) or {}
    models = harness.models_used(events)
    error = None
    if run.timed_out:
        error = "timeout"
    elif not events:
        error = f"no events (exit {run.returncode}): {run.stderr.strip()[:500]}"
    elif not run.stopped_early and harness.result_event(events) is None:
        error = f"stream ended without a result (exit {run.returncode})"
    loaded = sorted(init.get("skills") or [])
    return {
        "attempt": attempt,
        "slot": slot,
        "tool_prefix": prefix,
        "decisive_tool": tool.get("name") if tool else None,
        "skill": harness.skill_of(tool),
        "stopped_early": run.stopped_early,
        "duration_ms": run.wall_ms,
        "usage": harness.stream_usage(events),
        "first_request_usage": harness.first_request_usage(events),
        "models": models,
        "model_violations": harness.model_violations(models, ctx["model"]),
        "loaded_skills_match": loaded == sorted(catalog),
        "error": error,
        "stream": str(stream.relative_to(ctx["run_dir"])),
    }


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        harness.check_model_effort(args.model, args.effort)
        catalog_dir = args.catalog.resolve()
        sources = harness.catalog_skills(catalog_dir)
        if not sources:
            raise harness.UsageError(f"no skills found in {catalog_dir}")
        skills = args.skill or [
            n for n in sources if (sources[n] / "evals" / "eval_queries.json").is_file()
        ]
        unknown = [s for s in skills if s not in sources]
        if unknown:
            raise harness.UsageError(f"unknown skills: {', '.join(unknown)}")
        if not skills:
            raise harness.UsageError(
                "no skill has evals/eval_queries.json; pass --skill"
            )
        queries: list[Query] = []
        for skill in skills:
            path = sources[skill] / "evals" / "eval_queries.json"
            if not path.is_file():
                raise harness.UsageError(f"{path} does not exist")
            queries.extend(load_queries(skill, path))
        queries = select_queries(queries, args.split, args.limit)
        if not queries:
            raise harness.UsageError("no queries match the selection")
        settings = harness.default_settings(args.model, set(sources))
    except harness.UsageError as error:
        log(f"error: {error}")
        return harness.EXIT_USAGE
    except harness.IsolationError as error:
        log(f"isolation error: {error}")
        return harness.EXIT_ISOLATION

    if args.dry_run:
        settings_path = Path("<out>/settings.json")
        plan = {
            "catalog": str(catalog_dir),
            "catalog_skills": len(sources),
            "settings": settings,
            "settings_note": "before the preflight; at run time a zero-token /cost preflight may turn off further skills or plugins it finds loaded (for example bundled design and doctor, agents-md@builtin)",
            "runs_per_query": args.runs,
            "commands": [
                {
                    "skill": q.skill,
                    "index": q.index,
                    "split": q.split,
                    "command": shlex.join(
                        harness.claude_command(
                            q.query,
                            model=args.model,
                            effort=args.effort,
                            settings=settings_path,
                            permission_mode=args.permission_mode,
                        )
                    ),
                }
                for q in queries
            ],
        }
        print(json.dumps(plan, indent=2))
        return harness.EXIT_OK

    run_dir = args.out.resolve() / time.strftime(
        "triggers-%Y%m%dT%H%M%SZ", time.gmtime()
    )
    run_dir.mkdir(parents=True, exist_ok=False)
    log(f"output: {run_dir}")
    snapshot = harness.snapshot_skills(sources, run_dir / "catalog")
    settings_path = run_dir / "settings.json"
    slots_dir = harness.TRIGGER_SLOTS_DIR
    try:
        with harness.slot_project(slots_dir, 0, snapshot) as project:
            preflight = harness.preflight(
                project, settings_path, settings, set(snapshot), args.model, args.effort
            )
    except harness.IsolationError as error:
        log(f"isolation error: {error}")
        return harness.EXIT_ISOLATION
    isolation = harness.isolation_record(
        settings,
        {"catalog": preflight},
        f"{slots_dir}/slot-<n>, one fixed directory per --jobs slot (preflight in "
        "slot-0), deleted and recreated with identical content before each run so "
        "the system prompt, which includes the working directory, stays cacheable",
    )
    harness.write_json(run_dir / "isolation.json", isolation)
    log(
        f"preflight: {len(preflight['skills'])} catalog skills load, no plugins or MCP servers"
    )

    ctx = {
        "model": args.model,
        "effort": args.effort,
        "settings_path": settings_path,
        "permission_mode": args.permission_mode,
        "env": harness.child_env(args.model),
        "timeout": args.timeout,
        "streams": run_dir / "streams",
        "run_dir": run_dir,
        "slots_dir": slots_dir,
        "slots": slot_queue(args.jobs),
    }
    jobs = [(q, attempt) for q in queries for attempt in range(1, args.runs + 1)]
    log(
        f"running {len(jobs)} sessions ({len(queries)} queries x {args.runs} runs, {args.jobs} at a time)"
    )
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = [
            pool.submit(run_one, q, attempt, snapshot, ctx) for q, attempt in jobs
        ]
        outcomes = [future.result() for future in futures]

    results: list[dict[str, Any]] = []
    cursor = 0
    for query in queries:
        runs = outcomes[cursor : cursor + args.runs]
        cursor += args.runs
        scored = score_query(query, [r["skill"] for r in runs], args.threshold)
        scored["decisive_tools"] = dict(
            Counter(r["decisive_tool"] or "(none)" for r in runs)
        )
        scored["run_details"] = runs
        results.append(scored)
        mark = "PASS" if scored["passed"] else "FAIL"
        log(
            f"{mark} {query.skill}#{query.index} rate={scored['trigger_rate']:.2f} {query.query[:70]!r}"
        )

    errors = [r for r in outcomes if r["error"]]
    violations = sorted({m for r in outcomes for m in r["model_violations"]})
    mismatched = sum(
        1
        for r in outcomes
        if not r["loaded_skills_match"] and r["decisive_tool"] is not None
    )
    tokens = sum(r["usage"]["total_tokens"] for r in outcomes)
    summary = {
        "model": args.model,
        "effort": args.effort,
        "threshold": args.threshold,
        "runs_per_query": args.runs,
        "catalog": str(catalog_dir),
        "catalog_git": harness.git_state(catalog_dir),
        "output_dir": str(run_dir),
        "summary": summarize(results),
        "run_errors": len(errors),
        "model_violations": violations,
        "runs_with_unexpected_skill_list": mismatched,
        "tokens_total": tokens,
        "tokens_note": "runs stopped at the decisive tool call report usage from assistant events (partial)",
    }
    harness.write_json(
        run_dir / "results.json",
        {**summary, "queries": results, "isolation": isolation},
    )

    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        for item in results:
            mark = "PASS" if item["passed"] else "FAIL"
            want = "trigger" if item["should_trigger"] else "no-trigger"
            others = ",".join(item["other_skills_fired"]) or "-"
            print(
                f"{mark}\t{item['skill']}\t{item['split']}\t{want}\t{item['trigger_rate']:.2f}\tothers={others}\t{item['query'][:80]}"
            )
        overall = summary["summary"]["overall"]
        print(
            f"passed {overall['passed']}/{overall['queries']}; results: {run_dir / 'results.json'}"
        )

    if violations:
        log(f"model guard: runs used other models: {', '.join(violations)}")
        return harness.EXIT_ISOLATION
    if errors:
        log(f"{len(errors)} runs failed; see results.json")
        return harness.EXIT_RUN_ERROR
    return (
        harness.EXIT_OK
        if summary["summary"]["overall"]["failed"] == 0
        else harness.EXIT_FAILED
    )


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
