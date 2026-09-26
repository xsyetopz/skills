"""Run a skill's evals.json with and without the skill, grade, and benchmark.

Follows the agentskills.io "Evaluating skill output quality" method. Every
case in `<catalog>/<skill>/evals/evals.json` (default catalog: skills/) runs
in a fresh isolated workspace, once per configuration: `with_skill` (the skill
installed) and the baseline, `without_skill` (no skills) or `old_skill`
(--baseline-skill-dir, an older snapshot). Case `files` are paths relative
to the skill directory; a file under `evals/files/` is copied to the same
relative path inside the workspace, any other file to the workspace root.

Assertions are either plain strings, graded by one strict LLM grader call per
run (no skills, no tools, PASS only with quoted evidence), or objects
`{"text": "...", "check": "<shell command>"}` run in the run's workspace after
the session ends, where exit status 0 passes. Checks see EVAL_RESPONSE_FILE,
EVAL_TRANSCRIPT_FILE, and EVAL_OUTPUTS_DIR in their environment.

Task runs are sandboxed. Every Bash command runs in Claude Code's OS sandbox
with writes confined to the workspace and the sandbox temp dir and all network
access denied; a case with `"network": true` may reach any host. Deny rules
block git push, gh, dropdb, and (without network) curl, wget, WebFetch, and
WebSearch. The default acceptEdits permission mode denies Write/Edit outside
the workspace. isolation.json records the applied sandbox.

Layout (per the guide; with --runs above 1 each config holds run-<k>/):
  <out>/<skill>-workspace/iteration-N/
    eval-<id>/with_skill/{outputs/,timing.json,grading.json,transcript.jsonl,
                         grader_transcript.jsonl,run.json}
    eval-<id>/without_skill/...          (or old_skill/)
    benchmark.json, settings.json, settings-network.json, isolation.json
outputs/ holds response.md (the final reply) and files/ (files the run
created or changed). benchmark.json aggregates every graded run in the
iteration, so configurations can be run separately into the same iteration.

Examples:
  just eval-outputs --skill write-justfiles --dry-run
  just eval-outputs --skill write-justfiles --eval-id 1 --config with_skill
  just eval-outputs --skill write-justfiles --runs 3 --jobs 4
  just eval-outputs --skill write-justfiles --baseline-skill-dir /tmp/write-justfiles-old --iteration 2
  python3 scripts/evals/output_eval.py --catalog /tmp/candidate-skills --skill write-justfiles

stdout: a JSON summary (benchmark plus one row per run). stderr: progress.

Exit codes:
  0  every run completed and was graded
  2  usage error, invalid evals.json, or a run directory that already exists
  3  isolation or model guard failure (preflight, collision, other model used)
  4  a run or its grading failed (timeout, crash, grader error)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import shutil
import statistics
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import harness

WITH_SKILL = "with_skill"
CONFIG_NAMES = (WITH_SKILL, "without_skill", "old_skill")
CHECK_TIMEOUT = 300
MAX_COPY_BYTES = 5_000_000
GRADER_SCHEMA = {
    "type": "object",
    "properties": {
        "assertion_results": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "passed": {"type": "boolean"},
                    "evidence": {"type": "string"},
                },
                "required": ["text", "passed", "evidence"],
            },
        }
    },
    "required": ["assertion_results"],
}
GRADER_INSTRUCTIONS = """You are a strict grader for an AI agent's work. Grade each assertion below as PASS or FAIL against the run record that follows.

Rules:
- PASS only with concrete evidence: quote the exact command, tool result, file content, or reply text that satisfies the assertion.
- No benefit of the doubt. A label without substance, an intention without execution, or a claim the record does not show is a FAIL.
- An assertion about running or showing something passes only if the tool log shows it was run and what it printed.
- Judge only what the record shows; do not assume work that is not recorded.
- Return one result per assertion, in the given order, with the assertion text copied verbatim.

Respond with JSON only: {"assertion_results": [{"text": "...", "passed": true|false, "evidence": "..."}]}"""


@dataclass(frozen=True)
class Assertion:
    text: str
    check: str | None = None


@dataclass(frozen=True)
class Case:
    id: str
    prompt: str
    expected_output: str
    files: tuple[str, ...]
    assertions: tuple[Assertion, ...]
    network: bool = False


def load_evals(path: Path) -> tuple[str, list[Case]]:
    try:
        data = harness.read_json(path)
    except (OSError, ValueError) as error:
        raise harness.UsageError(f"{path}: {error}") from error
    if not isinstance(data, dict) or not isinstance(data.get("skill_name"), str):
        raise harness.UsageError(f"{path}: expected an object with 'skill_name'")
    if not isinstance(data.get("evals"), list):
        raise harness.UsageError(f"{path}: 'evals' must be a list")
    cases: list[Case] = []
    seen: set[str] = set()
    for index, item in enumerate(data["evals"]):
        where = f"{path} evals[{index}]"
        if not isinstance(item, dict):
            raise harness.UsageError(f"{where}: expected an object")
        raw_id = item.get("id")
        if (
            isinstance(raw_id, bool)
            or not isinstance(raw_id, (int, str))
            or str(raw_id) == ""
        ):
            raise harness.UsageError(
                f"{where}: 'id' must be an integer or non-empty string"
            )
        case_id = str(raw_id)
        if case_id in seen:
            raise harness.UsageError(f"{where}: duplicate id {case_id}")
        seen.add(case_id)
        prompt = item.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            raise harness.UsageError(f"{where}: 'prompt' must be a non-empty string")
        expected = item.get("expected_output", "")
        files = item.get("files", [])
        if not isinstance(expected, str):
            raise harness.UsageError(f"{where}: 'expected_output' must be a string")
        if not isinstance(files, list) or not all(isinstance(f, str) for f in files):
            raise harness.UsageError(f"{where}: 'files' must be a list of strings")
        network = item.get("network", False)
        if not isinstance(network, bool):
            raise harness.UsageError(f"{where}: 'network' must be true or false")
        cases.append(
            Case(
                case_id,
                prompt,
                expected,
                tuple(files),
                parse_assertions(item.get("assertions", []), where),
                network,
            )
        )
    return data["skill_name"], cases


def parse_assertions(raw: Any, where: str) -> tuple[Assertion, ...]:
    if not isinstance(raw, list):
        raise harness.UsageError(f"{where}: 'assertions' must be a list")
    parsed: list[Assertion] = []
    for index, item in enumerate(raw):
        if isinstance(item, str) and item.strip():
            parsed.append(Assertion(item))
        elif (
            isinstance(item, dict)
            and isinstance(item.get("text"), str)
            and isinstance(item.get("check"), str)
        ):
            if set(item) - {"text", "check"}:
                raise harness.UsageError(
                    f"{where} assertions[{index}]: only 'text' and 'check' are allowed"
                )
            parsed.append(Assertion(item["text"], item["check"]))
        else:
            raise harness.UsageError(
                f"{where} assertions[{index}]: expected a string or {{'text', 'check'}}"
            )
    return tuple(parsed)


def workspace_path(file: str) -> Path:
    path = Path(file)
    if path.is_absolute() or ".." in path.parts:
        raise harness.UsageError(
            f"case file {file!r} must be a relative path inside the skill"
        )
    parts = path.parts
    if parts[:2] == ("evals", "files") and len(parts) > 2:
        return Path(*parts[2:])
    return Path(path.name)


# --- workspace capture ---------------------------------------------------------


def manifest(root: Path) -> dict[str, str]:
    """Hashes of workspace files, skipping the installed skills and VCS metadata."""
    hashes: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if (
            rel.parts[0] in {".claude", ".git"}
            or not path.is_file()
            or path.is_symlink()
        ):
            continue
        hashes[rel.as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def changed_files(before: dict[str, str], after: dict[str, str]) -> list[str]:
    return sorted(rel for rel, digest in after.items() if before.get(rel) != digest)


def condensed_log(events: list[dict[str, Any]], limit: int = 60_000) -> str:
    """Tool calls and truncated results, in order, for the grader."""
    lines: list[str] = []
    for event in events:
        if event.get("type") == "assistant":
            for block in harness.tool_uses(event):
                payload = json.dumps(block.get("input"), ensure_ascii=False)
                lines.append(f"[tool {block.get('name')}] {payload[:1500]}")
        elif event.get("type") == "user" and not event.get("parent_tool_use_id"):
            content = (event.get("message") or {}).get("content")
            for block in content if isinstance(content, list) else []:
                if not isinstance(block, dict) or block.get("type") != "tool_result":
                    continue
                body = block.get("content")
                if isinstance(body, list):
                    body = "\n".join(
                        str(b.get("text", "")) for b in body if isinstance(b, dict)
                    )
                flag = " (error)" if block.get("is_error") else ""
                lines.append(f"[result{flag}] {str(body)[:2000]}")
    text = "\n".join(lines)
    return (
        text
        if len(text) <= limit
        else text[: limit // 2] + "\n...[truncated]...\n" + text[-limit // 2 :]
    )


def text_preview(path: Path, limit: int = 4000) -> str:
    """Text shown to the grader for a created file; binaries (e.g. .pyc) are
    summarised, because a NUL byte cannot travel in a command-line argument."""
    data = path.read_bytes()
    if b"\0" in data[:8192]:
        return f"<binary file, {len(data)} bytes>"
    return data.decode("utf-8", errors="replace")[:limit]


def grader_prompt(
    case: Case,
    assertions: list[Assertion],
    response: str,
    log: str,
    files: dict[str, str],
) -> str:
    numbered = "\n".join(f"{i}. {a.text}" for i, a in enumerate(assertions, 1))
    shown = (
        "\n\n".join(f"--- {name} ---\n{body}" for name, body in files.items())
        or "(none)"
    )
    return (
        f"{GRADER_INSTRUCTIONS}\n\n## Assertions\n{numbered}\n\n## Task given to the agent\n{case.prompt}\n\n"
        f"## Expected outcome (context only; grade the assertions)\n{case.expected_output}\n\n"
        f"## Tool log\n{log or '(no tool calls)'}\n\n## Files created or changed\n{shown}\n\n"
        f"## Final reply\n{response or '(empty)'}\n"
    )


def parse_grader(
    events: list[dict[str, Any]], assertions: list[Assertion]
) -> list[dict[str, Any]]:
    result = harness.result_event(events) or {}
    payload = result.get("structured_output")
    if not isinstance(payload, dict):
        text = str(result.get("result") or "")
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ValueError("grader returned no JSON")
        payload = json.loads(match.group(0))
    items = payload.get("assertion_results") if isinstance(payload, dict) else None
    if not isinstance(items, list) or len(items) != len(assertions):
        raise ValueError(
            f"grader returned {len(items) if isinstance(items, list) else 'no'} results for {len(assertions)} assertions"
        )
    graded: list[dict[str, Any]] = []
    for assertion, item in zip(assertions, items, strict=True):
        evidence = (
            str(item.get("evidence") or "").strip() if isinstance(item, dict) else ""
        )
        passed = (
            isinstance(item, dict) and item.get("passed") is True and bool(evidence)
        )
        graded.append(
            {
                "text": assertion.text,
                "passed": passed,
                "evidence": evidence or "no evidence given",
            }
        )
    return graded


def run_check(
    assertion: Assertion, workspace: Path, env: dict[str, str]
) -> dict[str, Any]:
    assert assertion.check is not None
    try:
        done = subprocess.run(
            assertion.check,
            shell=True,
            cwd=workspace,
            env=env,
            capture_output=True,
            text=True,
            timeout=CHECK_TIMEOUT,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {
            "text": assertion.text,
            "passed": False,
            "evidence": f"check timed out after {CHECK_TIMEOUT}s: {assertion.check}",
        }
    tail = (done.stdout + done.stderr).strip()[-600:]
    evidence = f"`{assertion.check}` exited {done.returncode}" + (
        f": {tail}" if tail else ""
    )
    return {
        "text": assertion.text,
        "passed": done.returncode == 0,
        "evidence": evidence,
    }


def grading_document(results: list[dict[str, Any]]) -> dict[str, Any]:
    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    return {
        "assertion_results": results,
        "summary": {
            "passed": passed,
            "failed": total - passed,
            "total": total,
            "pass_rate": round(passed / total, 4) if total else None,
        },
    }


# --- benchmark ----------------------------------------------------------------


def stats(values: list[float]) -> dict[str, float] | None:
    if not values:
        return None
    stddev = statistics.stdev(values) if len(values) > 1 else 0.0
    return {"mean": round(statistics.fmean(values), 4), "stddev": round(stddev, 4)}


def run_dirs(iteration: Path) -> dict[str, list[Path]]:
    """Graded run directories per configuration (config dir itself, or its run-<k>/)."""
    found: dict[str, list[Path]] = {}
    for config_dir in sorted(iteration.glob("eval-*/*")):
        if config_dir.name not in CONFIG_NAMES or not config_dir.is_dir():
            continue
        candidates = [config_dir, *sorted(config_dir.glob("run-*"))]
        for run in candidates:
            if (run / "grading.json").is_file() and (run / "timing.json").is_file():
                found.setdefault(config_dir.name, []).append(run)
    return found


def benchmark(iteration: Path) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for config, runs in sorted(run_dirs(iteration).items()):
        rates: list[float] = []
        seconds: list[float] = []
        tokens: list[float] = []
        for run in runs:
            grading = harness.read_json(run / "grading.json")
            timing = harness.read_json(run / "timing.json")
            if grading["summary"]["pass_rate"] is not None:
                rates.append(grading["summary"]["pass_rate"])
            seconds.append(timing["duration_ms"] / 1000)
            tokens.append(timing["total_tokens"])
        summary[config] = {
            "pass_rate": stats(rates),
            "time_seconds": stats(seconds),
            "tokens": stats(tokens),
            "runs": len(runs),
        }
    baseline = next((c for c in ("old_skill", "without_skill") if c in summary), None)
    if WITH_SKILL in summary and baseline:
        delta: dict[str, float | None] = {}
        for metric in ("pass_rate", "time_seconds", "tokens"):
            ours, theirs = summary[WITH_SKILL][metric], summary[baseline][metric]
            delta[metric] = (
                round(ours["mean"] - theirs["mean"], 4) if ours and theirs else None
            )
        summary["delta"] = delta
    return {"run_summary": summary}


# --- runs ---------------------------------------------------------------------


@dataclass(frozen=True)
class Job:
    case: Case
    config: str
    run: int
    run_dir: Path
    skills: dict[str, Path]


def execute(job: Job, ctx: dict[str, Any]) -> dict[str, Any]:
    workspace = harness.make_project(job.skills, prefix=f"skill-output-{job.config}-")
    try:
        for file in job.case.files:
            target = workspace / workspace_path(file)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ctx["skill_dir"] / file, target)
        before = manifest(workspace)
        command = harness.claude_command(
            job.case.prompt,
            model=ctx["model"],
            effort=ctx["effort"],
            settings=ctx[
                "network_settings_path" if job.case.network else "settings_path"
            ],
            permission_mode=ctx["permission_mode"],
        )
        run = harness.run_claude(command, workspace, ctx["env"], ctx["timeout"])
        return record(job, run, workspace, before, ctx)
    finally:
        harness.remove_project(workspace)


def record(
    job: Job,
    run: harness.RunResult,
    workspace: Path,
    before: dict[str, str],
    ctx: dict[str, Any],
) -> dict[str, Any]:
    events = run.events
    outputs = job.run_dir / "outputs"
    (outputs / "files").mkdir(parents=True, exist_ok=True)
    transcript = job.run_dir / "transcript.jsonl"
    transcript.write_text("".join(run.lines), encoding="utf-8")
    response = harness.final_text(events)
    (outputs / "response.md").write_text(response, encoding="utf-8")
    created: dict[str, str] = {}
    skipped: list[str] = []
    for rel in changed_files(before, manifest(workspace)):
        source = workspace / rel
        if source.stat().st_size > MAX_COPY_BYTES:
            skipped.append(rel)
            continue
        target = outputs / "files" / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        created[rel] = text_preview(source)

    result = harness.result_event(events) or {}
    usage = harness.stream_usage(events)
    duration = int(result.get("duration_ms") or run.wall_ms)
    harness.write_json(
        job.run_dir / "timing.json",
        {"total_tokens": usage["total_tokens"], "duration_ms": duration},
    )

    errors: list[str] = []
    if run.timed_out:
        errors.append("session timed out")
    if not result:
        errors.append(
            f"no result event (exit {run.returncode}): {run.stderr.strip()[:500]}"
        )
    elif result.get("is_error"):
        errors.append(f"session ended with {result.get('subtype')}")

    env = {
        **os.environ,
        "EVAL_RESPONSE_FILE": str(outputs / "response.md"),
        "EVAL_TRANSCRIPT_FILE": str(transcript),
        "EVAL_OUTPUTS_DIR": str(outputs),
    }
    graded: list[dict[str, Any] | None] = [
        run_check(a, workspace, env) if a.check else None for a in job.case.assertions
    ]
    judged = [a for a in job.case.assertions if a.check is None]
    grader: dict[str, Any] | None = None
    if judged:
        prompt = grader_prompt(
            job.case,
            judged,
            response,
            condensed_log(events),
            dict(list(created.items())[:10]),
        )
        grader, verdicts = grade(
            prompt, judged, ctx, job.run_dir / "grader_transcript.jsonl"
        )
        if grader.get("error"):
            errors.append(f"grader: {grader['error']}")
        slots = iter(verdicts)
        graded = [item if item is not None else next(slots) for item in graded]
    grading = grading_document([g for g in graded if g is not None])
    harness.write_json(job.run_dir / "grading.json", grading)

    models = harness.models_used(events)
    grader_models = grader["models"] if grader else []
    violations = harness.model_violations(
        sorted({*models, *grader_models}), ctx["model"]
    )
    meta = {
        "eval_id": job.case.id,
        "config": job.config,
        "run": job.run,
        "command": shlex.join(run.command),
        "skills_loaded": (harness.init_event(events) or {}).get("skills"),
        "permission_mode": ctx["permission_mode"],
        "usage": usage,
        "num_turns": result.get("num_turns"),
        "network": job.case.network,
        "permission_denials": result.get("permission_denials"),
        "models": models,
        "model_violations": violations,
        "files_skipped_over_size_limit": skipped,
        "grader": grader,
        "errors": errors,
    }
    harness.write_json(job.run_dir / "run.json", meta)
    return {
        "eval_id": job.case.id,
        "config": job.config,
        "run": job.run,
        "pass_rate": grading["summary"]["pass_rate"],
        "passed": grading["summary"]["passed"],
        "total": grading["summary"]["total"],
        "total_tokens": usage["total_tokens"],
        "duration_ms": duration,
        "grader_tokens": grader["usage"]["total_tokens"] if grader else 0,
        "model_violations": violations,
        "errors": errors,
        "dir": str(job.run_dir),
    }


def grade(
    prompt: str, assertions: list[Assertion], ctx: dict[str, Any], transcript: Path
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    project = harness.make_project({}, prefix="skill-grader-")
    try:
        command = harness.claude_command(
            prompt.replace("\0", ""),
            model=ctx["model"],
            effort=ctx["effort"],
            settings=ctx["settings_path"],
            permission_mode="dontAsk",
            extra=("--tools", "", "--json-schema", json.dumps(GRADER_SCHEMA)),
        )
        run = harness.run_claude(command, project, ctx["env"], ctx["timeout"])
    finally:
        harness.remove_project(project)
    transcript.write_text("".join(run.lines), encoding="utf-8")
    events = run.events
    meta: dict[str, Any] = {
        "usage": harness.stream_usage(events),
        "models": harness.models_used(events),
        "error": None,
    }
    try:
        return meta, parse_grader(events, assertions)
    except (ValueError, TypeError) as error:
        meta["error"] = f"{error}; exit {run.returncode}; {run.stderr.strip()[:300]}"
        failed = [
            {"text": a.text, "passed": False, "evidence": f"grader error: {error}"}
            for a in assertions
        ]
        return meta, failed


# --- main ---------------------------------------------------------------------


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(__doc__ or "").partition("\n\n")[0],
        epilog=(__doc__ or "").partition("\n\n")[2],
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--skill", required=True, help="skill directory name under the catalog"
    )
    parser.add_argument(
        "--eval-id",
        action="append",
        default=[],
        help="case id to run (repeatable; default: all)",
    )
    parser.add_argument(
        "--config",
        action="append",
        choices=(WITH_SKILL, "baseline"),
        default=[],
        help="configuration to run (repeatable; default: both)",
    )
    parser.add_argument(
        "--baseline-skill-dir",
        type=Path,
        help="older skill snapshot to use as the baseline (old_skill) instead of no skill",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=1,
        help="runs per case and configuration (default: 1)",
    )
    parser.add_argument(
        "--jobs", type=int, default=2, help="concurrent sessions (default: 2)"
    )
    parser.add_argument(
        "--iteration",
        type=int,
        help="iteration number (default: one past the highest existing)",
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
        default=1800,
        help="seconds before a session is stopped (default: 1800)",
    )
    parser.add_argument(
        "--permission-mode",
        default="acceptEdits",
        help=(
            "claude --permission-mode for task runs (default: acceptEdits, so file "
            "edits outside the workspace are denied; auto sends them to the classifier)"
        ),
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
        help="print the settings, layout, and commands; make no model calls",
    )
    args = parser.parse_args(argv)
    if (
        args.runs < 1
        or args.jobs < 1
        or (args.iteration is not None and args.iteration < 1)
    ):
        parser.error("--runs, --jobs, and --iteration must be positive")
    return args


def next_iteration(workspace: Path) -> int:
    numbers = [
        int(p.name.split("-", 1)[1])
        for p in workspace.glob("iteration-*")
        if p.name.split("-", 1)[1].isdigit()
    ]
    return max(numbers, default=0) + 1


def log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        harness.check_model_effort(args.model, args.effort)
        skill_dir = args.catalog.resolve() / args.skill
        if not (skill_dir / "SKILL.md").is_file():
            raise harness.UsageError(f"{skill_dir} has no SKILL.md")
        name, cases = load_evals(skill_dir / "evals" / "evals.json")
        if name != args.skill:
            raise harness.UsageError(
                f"evals.json skill_name {name!r} does not match {args.skill!r}"
            )
        if args.eval_id:
            unknown = sorted(set(args.eval_id) - {c.id for c in cases})
            if unknown:
                raise harness.UsageError(f"unknown eval ids: {', '.join(unknown)}")
            cases = [c for c in cases if c.id in args.eval_id]
        for case in cases:
            for file in case.files:
                workspace_path(file)
                if not (skill_dir / file).is_file():
                    raise harness.UsageError(
                        f"eval {case.id}: file {file} does not exist"
                    )
        baseline_dir = (
            args.baseline_skill_dir.resolve() if args.baseline_skill_dir else None
        )
        if baseline_dir and not (baseline_dir / "SKILL.md").is_file():
            raise harness.UsageError(f"{baseline_dir} has no SKILL.md")
        baseline = "old_skill" if baseline_dir else "without_skill"
        configs = [
            WITH_SKILL if c == WITH_SKILL else baseline
            for c in (args.config or [WITH_SKILL, "baseline"])
        ]
        configs = list(dict.fromkeys(configs))
        settings = {
            **harness.default_settings(args.model, {args.skill}),
            **harness.sandbox_settings(network=False),
        }
    except harness.UsageError as error:
        log(f"error: {error}")
        return harness.EXIT_USAGE
    except harness.IsolationError as error:
        log(f"isolation error: {error}")
        return harness.EXIT_ISOLATION

    workspace_root = args.out.resolve() / f"{args.skill}-workspace"
    iteration = (
        workspace_root / f"iteration-{args.iteration or next_iteration(workspace_root)}"
    )

    def run_dir(case: Case, config: str, number: int) -> Path:
        base = iteration / f"eval-{case.id}" / config
        return base if args.runs == 1 else base / f"run-{number}"

    planned = [
        (c, cfg, k) for c in cases for cfg in configs for k in range(1, args.runs + 1)
    ]
    existing = [run_dir(*p) for p in planned if run_dir(*p).exists()]
    if existing:
        log(
            f"error: run directories already exist (use another --iteration): {existing[0]}"
        )
        return harness.EXIT_USAGE

    if args.dry_run:
        plan = {
            "iteration_dir": str(iteration),
            "settings": settings,
            "network_settings_changes": harness.sandbox_settings(network=True),
            "settings_note": "before the preflight; at run time a zero-token /cost preflight may turn off further skills or plugins it finds loaded (for example bundled design and doctor, agents-md@builtin)",
            "runs": [
                {
                    "eval_id": c.id,
                    "config": cfg,
                    "run": k,
                    "dir": str(run_dir(c, cfg, k)),
                    "files": list(c.files),
                    "network": c.network,
                    "checks": [a.check for a in c.assertions if a.check],
                    "llm_graded_assertions": sum(
                        1 for a in c.assertions if a.check is None
                    ),
                    "command": shlex.join(
                        harness.claude_command(
                            c.prompt,
                            model=args.model,
                            effort=args.effort,
                            settings=iteration
                            / (
                                "settings-network.json"
                                if c.network
                                else "settings.json"
                            ),
                            permission_mode=args.permission_mode,
                        )
                    ),
                }
                for c, cfg, k in planned
            ],
        }
        print(json.dumps(plan, indent=2))
        return harness.EXIT_OK

    iteration.mkdir(parents=True, exist_ok=True)
    log(f"iteration: {iteration}")
    snapshot_root = Path(tempfile.mkdtemp(prefix="skill-output-snapshot-"))
    try:
        skill_sets: dict[str, dict[str, Path]] = {"without_skill": {}}
        skill_sets[WITH_SKILL] = harness.snapshot_skills(
            {args.skill: skill_dir}, snapshot_root / "current"
        )
        if baseline_dir:
            skill_sets["old_skill"] = harness.snapshot_skills(
                {args.skill: baseline_dir}, snapshot_root / "old"
            )
        settings_path = iteration / "settings.json"
        preflights: dict[str, Any] = {}
        try:
            for config in [*configs, "without_skill"]:
                if config in preflights:
                    continue
                project = harness.make_project(
                    skill_sets[config], prefix="skill-output-preflight-"
                )
                try:
                    preflights[config] = harness.preflight(
                        project,
                        settings_path,
                        settings,
                        set(skill_sets[config]),
                        args.model,
                        args.effort,
                    )
                finally:
                    harness.remove_project(project)
        except harness.IsolationError as error:
            log(f"isolation error: {error}")
            return harness.EXIT_ISOLATION
        preflights["grader"] = (
            "same as without_skill; also --tools '' and --json-schema"
        )
        network_settings_path = iteration / "settings-network.json"
        network_settings = {**settings, **harness.sandbox_settings(network=True)}
        harness.write_json(network_settings_path, network_settings)
        isolation = harness.isolation_record(
            settings,
            preflights,
            "fresh temp directory per run, outside the repository",
        )
        isolation["sandbox"] = {
            "permission_mode": args.permission_mode,
            "settings_files": {
                "settings.json": "cases without network (and the grader)",
                "settings-network.json": 'cases with "network": true',
            },
            "default": harness.sandbox_settings(network=False),
            "network": harness.sandbox_settings(network=True),
            "network_cases": sorted({c.id for c, _, _ in planned if c.network}),
            "preflight": "the /cost preflight ran with the sandbox enabled and failIfUnavailable true",
            "enforcement": (
                "Bash runs only inside the OS sandbox, and a Bash allow rule approves "
                "every sandboxed command: writes are limited to the run "
                "workspace and the sandbox's per-user temp dir (its TMPDIR, /tmp/claude-<uid> on "
                "macOS, shared with other Claude Code sessions), and hosts outside the "
                "allowlist are denied (the allowlist is empty unless the case sets "
                "network). rm -rf outside the workspace fails in the sandbox, and "
                "critical-path removals are denied by Claude Code itself. The Write and "
                "Edit tools are not sandboxed; the acceptEdits permission mode approves "
                "them only inside the working directory, and with --permission-prompts "
                "none anything else is denied. Deny rules block the usual spellings of "
                "git push, gh, dropdb, and (without network) curl, wget, WebFetch, and "
                "WebSearch. User settings.json permission rules still merge in."
            ),
        }
        isolation["catalog_git"] = harness.git_state(skill_dir)
        harness.write_json(iteration / "isolation.json", isolation)

        ctx = {
            "model": args.model,
            "effort": args.effort,
            "settings_path": settings_path,
            "network_settings_path": network_settings_path,
            "permission_mode": args.permission_mode,
            "env": harness.child_env(args.model),
            "timeout": args.timeout,
            "skill_dir": skill_dir,
        }
        jobs = [
            Job(c, cfg, k, run_dir(c, cfg, k), skill_sets[cfg]) for c, cfg, k in planned
        ]
        log(
            f"running {len(jobs)} sessions ({args.jobs} at a time), model {args.model}, effort {args.effort}"
        )
        with ThreadPoolExecutor(max_workers=args.jobs) as pool:
            rows = list(pool.map(lambda job: execute(job, ctx), jobs))
    finally:
        shutil.rmtree(snapshot_root, ignore_errors=True)

    for row in rows:
        log(
            f"eval-{row['eval_id']} {row['config']} run {row['run']}: {row['passed']}/{row['total']} passed, {row['total_tokens']} tokens"
        )
    bench = benchmark(iteration)
    bench["metadata"] = {
        "skill": args.skill,
        "model": args.model,
        "effort": args.effort,
        "permission_mode": args.permission_mode,
        "runs_per_config": args.runs,
        "isolation": "see isolation.json",
    }
    harness.write_json(iteration / "benchmark.json", bench)
    print(
        json.dumps(
            {"iteration_dir": str(iteration), "benchmark": bench, "runs": rows},
            indent=2,
        )
    )

    if any(row["model_violations"] for row in rows):
        log("model guard: a run used a model other than the target; see run.json")
        return harness.EXIT_ISOLATION
    if any(row["errors"] for row in rows):
        log("some runs failed; see run.json in each run directory")
        return harness.EXIT_RUN_ERROR
    return harness.EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
