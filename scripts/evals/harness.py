"""Shared Claude Code isolation, process, and stream-json helpers for skill evals.

Both eval scripts run `claude -p` in throwaway project directories whose
`.claude/skills/` holds exactly the skills under test. A generated settings
file turns off everything else the user's machine would add: bundled skills,
personal and claude.ai-synced skills, plugins, hooks, and claude.ai MCP
connectors. `--strict-mcp-config` drops the remaining MCP servers. A zero-cost
preflight (`/cost`, a local command that never reaches the model) reads the
stream's `init` event and proves which skills, plugins, and MCP servers load
before any model call is made. The user-level CLAUDE.md still loads; the
isolation record says so.
"""

from __future__ import annotations

import contextlib
import fcntl
import json
import os
import re
import shutil
import signal
import subprocess
import tempfile
import threading
import time
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
CATALOG_DIR = REPO_ROOT / "skills"
DEFAULT_OUT = REPO_ROOT / ".evals"
# Fixed trigger-run working directories, outside any repository so no parent
# CLAUDE.md, skills, or git status reaches the session.
TRIGGER_SLOTS_DIR = Path(tempfile.gettempdir()) / "skill-evals-trigger"

ALLOWED_MODELS = ("claude-opus-5-5", "claude-fable-5-1")
ALLOWED_EFFORTS = ("low", "medium", "high", "xhigh")
DEFAULT_MODEL = "claude-opus-5-5"
DEFAULT_EFFORT = "high"

# Claude Code resolves these for background work, subagents, and the
# sonnet/haiku aliases; pinning them keeps every request on the target model.
MODEL_ENV_KEYS = (
    "ANTHROPIC_DEFAULT_HAIKU_MODEL",
    "ANTHROPIC_DEFAULT_SONNET_MODEL",
    "ANTHROPIC_DEFAULT_OPUS_MODEL",
    "ANTHROPIC_SMALL_FAST_MODEL",
    "CLAUDE_CODE_SUBAGENT_MODEL",
)

# Skill snapshots never carry eval definitions: a with-skill run must not be
# able to read the assertions it is graded against.
SNAPSHOT_IGNORE = shutil.ignore_patterns("evals", "__pycache__", "*.pyc", ".DS_Store")

# Tools a session may call before deciding what to do; trigger scoring reads
# past them to the first Skill call or other tool.
META_TOOLS = frozenset(
    {
        "ToolSearch",
        "TodoWrite",
        "TaskCreate",
        "TaskUpdate",
        "TaskList",
        "TaskGet",
    }
)

EXIT_OK = 0
EXIT_FAILED = 1
EXIT_USAGE = 2
EXIT_ISOLATION = 3
EXIT_RUN_ERROR = 4


class UsageError(Exception):
    """Invalid arguments or eval definitions (exit 2)."""


class IsolationError(Exception):
    """The session would not be isolated or would use a disallowed model (exit 3)."""


def check_model_effort(model: str, effort: str) -> None:
    if model not in ALLOWED_MODELS:
        raise UsageError(
            f"model {model!r} is not allowed; choose one of {', '.join(ALLOWED_MODELS)}"
        )
    if effort == "max":
        raise UsageError("effort 'max' is not allowed; use low, medium, high, or xhigh")
    if effort not in ALLOWED_EFFORTS:
        raise UsageError(
            f"effort {effort!r} is not one of {', '.join(ALLOWED_EFFORTS)}"
        )


# --- settings -----------------------------------------------------------------


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def personal_skill_names(claude_home: Path) -> list[str]:
    """Skill names under ~/.claude/skills, including claude.ai-synced skills."""
    root = claude_home / "skills"
    names: set[str] = set()
    if not root.is_dir():
        return []
    for entry in root.iterdir():
        if entry.name.startswith("."):
            continue
        if entry.name == "synced":
            for bucket in entry.iterdir():
                if bucket.is_dir():
                    names.update(
                        child.name
                        for child in bucket.iterdir()
                        if (child / "SKILL.md").is_file()
                    )
            continue
        if (entry / "SKILL.md").is_file():
            names.add(entry.name)
    return sorted(names)


def plugin_ids(settings_files: list[Path], installed_manifest: Path) -> list[str]:
    """Plugins enabled in any settings file or installed at user level."""
    ids: set[str] = set()
    for path in settings_files:
        if not path.is_file():
            continue
        enabled = read_json(path).get("enabledPlugins") or {}
        ids.update(name for name, on in enabled.items() if on)
    if installed_manifest.is_file():
        ids.update((read_json(installed_manifest).get("plugins") or {}).keys())
    return sorted(ids)


def build_settings(
    model: str,
    skills_off: list[str],
    plugins_off: list[str],
) -> dict[str, Any]:
    env: dict[str, str] = dict.fromkeys(MODEL_ENV_KEYS, model)
    env["ENABLE_CLAUDEAI_MCP_SERVERS"] = "false"
    return {
        "disableBundledSkills": True,
        "disableAllHooks": True,
        "skillOverrides": dict.fromkeys(sorted(set(skills_off)), "off"),
        "enabledPlugins": dict.fromkeys(sorted(set(plugins_off)), False),
        "env": env,
    }


def sandbox_settings(network: bool) -> dict[str, Any]:
    """Claude Code sandbox and permission rules for model-driven task runs.

    Every Bash command runs in the OS sandbox (`allowUnsandboxedCommands`
    false removes the unsandboxed retry; `failIfUnavailable` refuses to start
    without it), which confines writes to the working directory and the
    sandbox's per-user temp dir. `strictAllowlist` with no allowed domains
    denies all network access; `network` opts in with a `WebFetch(domain:*)`
    allow rule, which the sandbox also honors for Bash. The `Bash` allow rule
    approves every command, which is safe only because each one is sandboxed;
    without it, commands Claude Code recognizes as network access (`curl URL`,
    `python3 -c` with a URL) need approval and are denied even with network
    opted in. Deny rules stop the usual spellings of outward or destructive
    commands; the sandbox enforces the boundary for other spellings.
    """
    deny = [
        "Bash(git push *)",
        "Bash(gh)",
        "Bash(gh *)",
        "Bash(dropdb *)",
    ]
    allow = ["Skill", "Bash"]
    if network:
        allow += ["WebFetch(domain:*)", "WebSearch"]
    else:
        deny += ["Bash(curl *)", "Bash(wget *)", "WebFetch", "WebSearch"]
    return {
        "sandbox": {
            "enabled": True,
            "failIfUnavailable": True,
            "autoAllowBashIfSandboxed": True,
            "allowUnsandboxedCommands": False,
            "network": {"strictAllowlist": True, "allowedDomains": []},
        },
        "permissions": {"allow": allow, "deny": deny},
    }


def default_settings(model: str, under_test: set[str]) -> dict[str, Any]:
    home = Path.home() / ".claude"
    personal = personal_skill_names(home)
    collisions = sorted(under_test.intersection(personal))
    if collisions:
        raise IsolationError(
            "personal skills shadow catalog skills of the same name (personal wins over "
            f"project): {', '.join(collisions)}"
        )
    settings_files = [
        home / "settings.json",
        REPO_ROOT / ".claude" / "settings.json",
        REPO_ROOT / ".claude" / "settings.local.json",
    ]
    plugins = plugin_ids(settings_files, home / "plugins" / "installed_plugins.json")
    return build_settings(model, personal, plugins)


def child_env(model: str) -> dict[str, str]:
    env = dict(os.environ)
    env.update(dict.fromkeys(MODEL_ENV_KEYS, model))
    env["ENABLE_CLAUDEAI_MCP_SERVERS"] = "false"
    return env


# --- projects -----------------------------------------------------------------


def catalog_skills(catalog: Path) -> dict[str, Path]:
    return {
        path.parent.name: path.parent for path in sorted(catalog.glob("*/SKILL.md"))
    }


def snapshot_skills(sources: dict[str, Path], dest: Path) -> dict[str, Path]:
    """Copy skills (without evals/) so concurrent edits cannot change a run."""
    dest.mkdir(parents=True, exist_ok=True)
    copies: dict[str, Path] = {}
    for name, source in sources.items():
        target = dest / name
        shutil.copytree(source, target, ignore=SNAPSHOT_IGNORE)
        copies[name] = target
    return copies


def install_skills(project: Path, skills: dict[str, Path]) -> None:
    """Copy each skill into the project without its `evals/` directory.

    A symlink would let a with-skill run read the hidden checks and expected
    values in evals/ (answer leakage) and write through into the repository.
    """
    skills_dir = project / ".claude" / "skills"
    skills_dir.mkdir(parents=True)
    for name, source in sorted(skills.items()):
        root = source.resolve()

        def ignore(directory: str, names: list[str], root: Path = root) -> set[str]:
            skipped = {"__pycache__", "node_modules"} & set(names)
            if Path(directory) == root and "evals" in names:
                skipped.add("evals")
            return skipped

        shutil.copytree(root, skills_dir / name, symlinks=True, ignore=ignore)


def make_project(skills: dict[str, Path], prefix: str) -> Path:
    """A fresh directory outside the repository with the given skills copied in.

    It lives in the system temp dir so no repository CLAUDE.md, AGENTS.md, or
    `.claude/skills` from a parent directory is discovered.
    """
    project = Path(tempfile.mkdtemp(prefix=prefix))
    install_skills(project, skills)
    return project


@contextlib.contextmanager
def slot_project(root: Path, slot: int, skills: dict[str, Path]) -> Iterator[Path]:
    """The fixed directory `<root>/slot-<slot>`, recreated with identical content.

    Claude Code puts the working directory (and memory paths derived from it)
    in the system prompt, so a fresh directory per run defeats prompt caching.
    Reusing one path per concurrent slot keeps the prompt byte-identical across
    runs. An exclusive lock on `slot-<slot>.lock` keeps two harness processes
    from sharing a slot at the same time.
    """
    root.mkdir(parents=True, exist_ok=True)
    with (root / f"slot-{slot}.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        project = root / f"slot-{slot}"
        remove_project(project)
        project.mkdir()
        try:
            install_skills(project, skills)
            yield project
        finally:
            remove_project(project)


def session_state_dir(project: Path, claude_home: Path) -> Path:
    """Where Claude Code keeps per-directory state for `project`."""
    return (
        claude_home / "projects" / re.sub(r"[^A-Za-z0-9]", "-", str(project.resolve()))
    )


def remove_project(project: Path) -> None:
    """Delete a run directory and the state Claude Code created for it.

    `--no-session-persistence` skips the transcript, but Claude Code still
    creates `~/.claude/projects/<sanitized cwd>/` (and large tool results) and
    a per-session temp dir under `/tmp/claude-<uid>/<sanitized cwd>/`.
    """
    state = session_state_dir(project, Path.home() / ".claude")
    temp = Path("/tmp") / f"claude-{os.getuid()}" / state.name
    for path in (project, state, temp):
        shutil.rmtree(path, ignore_errors=True)


def claude_command(
    prompt: str,
    *,
    model: str,
    effort: str,
    settings: Path,
    permission_mode: str,
    extra: tuple[str, ...] = (),
) -> list[str]:
    return [
        "claude",
        "-p",
        prompt,
        "--output-format",
        "stream-json",
        "--verbose",
        "--model",
        model,
        "--effort",
        effort,
        "--settings",
        str(settings),
        "--strict-mcp-config",
        "--no-session-persistence",
        "--permission-mode",
        permission_mode,
        "--permission-prompts",
        "none",
        *extra,
    ]


# --- stream-json --------------------------------------------------------------


def parse_stream(lines: list[str]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for line in lines:
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict):
            events.append(event)
    return events


def tool_uses(event: dict[str, Any]) -> list[dict[str, Any]]:
    """Top-level tool_use blocks in an assistant event (subagent events excluded)."""
    if event.get("type") != "assistant" or event.get("parent_tool_use_id"):
        return []
    content = (event.get("message") or {}).get("content") or []
    return [
        block
        for block in content
        if isinstance(block, dict) and block.get("type") == "tool_use"
    ]


def tool_prefix(
    events: list[dict[str, Any]],
) -> tuple[list[str], dict[str, Any] | None]:
    """Top-level tool names up to the first decisive call, and that call.

    Meta tools (tool lookup and todo bookkeeping) are read past; the first
    `Skill` call or other tool is decisive. With no decisive call yet, the
    names seen so far and None are returned. `Task` is the subagent tool in
    Claude Code, so it is decisive, not a todo tool.
    """
    names: list[str] = []
    for event in events:
        for use in tool_uses(event):
            name = str(use.get("name"))
            names.append(name)
            if name not in META_TOOLS:
                return names, use
    return names, None


def skill_of(tool_use: dict[str, Any] | None) -> str | None:
    """Skill name for a Skill tool call, without any `namespace:` prefix."""
    if not tool_use or tool_use.get("name") != "Skill":
        return None
    name = str((tool_use.get("input") or {}).get("skill") or "")
    return name.rsplit(":", 1)[-1] or None


def init_event(events: list[dict[str, Any]]) -> dict[str, Any] | None:
    return next(
        (e for e in events if e.get("type") == "system" and e.get("subtype") == "init"),
        None,
    )


def result_event(events: list[dict[str, Any]]) -> dict[str, Any] | None:
    return next((e for e in reversed(events) if e.get("type") == "result"), None)


def token_total(usage: dict[str, Any]) -> int:
    keys = (
        "input_tokens",
        "cache_creation_input_tokens",
        "cache_read_input_tokens",
        "output_tokens",
    )
    return sum(int(usage.get(key) or 0) for key in keys)


def usage_components(usage: dict[str, Any]) -> dict[str, int]:
    keys = (
        "input_tokens",
        "cache_creation_input_tokens",
        "cache_read_input_tokens",
        "output_tokens",
    )
    return {key: int(usage.get(key) or 0) for key in keys}


def stream_usage(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Token usage from the result event, or summed per API message when the run was cut short."""
    result = result_event(events)
    if result and isinstance(result.get("usage"), dict):
        usage = result["usage"]
        return {
            "total_tokens": token_total(usage),
            "components": usage_components(usage),
            "total_cost_usd": result.get("total_cost_usd"),
            "partial": False,
        }
    per_message: dict[str, dict[str, Any]] = {}
    for event in events:
        message = event.get("message") or {}
        if event.get("type") == "assistant" and isinstance(message.get("usage"), dict):
            per_message[str(message.get("id"))] = message["usage"]
    components = {
        key: sum(usage_components(u)[key] for u in per_message.values())
        for key in (
            "input_tokens",
            "cache_creation_input_tokens",
            "cache_read_input_tokens",
            "output_tokens",
        )
    }
    return {
        "total_tokens": sum(components.values()),
        "components": components,
        "total_cost_usd": None,
        "partial": True,
    }


def first_request_usage(events: list[dict[str, Any]]) -> dict[str, int] | None:
    """Token components of the session's first top-level API response.

    Later requests in the same session read the cache the first one wrote, so
    only the first request shows whether a run reused a cache from earlier runs.
    """
    first_id: str | None = None
    usage: dict[str, Any] | None = None
    for event in events:
        message = event.get("message") or {}
        if (
            event.get("type") != "assistant"
            or event.get("parent_tool_use_id")
            or not isinstance(message.get("usage"), dict)
        ):
            continue
        first_id = first_id or str(message.get("id"))
        if str(message.get("id")) == first_id:
            usage = message["usage"]
    return usage_components(usage) if usage is not None else None


def models_used(events: list[dict[str, Any]]) -> list[str]:
    models: set[str] = set()
    result = result_event(events)
    if result:
        models.update((result.get("modelUsage") or {}).keys())
    for event in events:
        if event.get("type") == "assistant":
            model = (event.get("message") or {}).get("model")
            if model:
                models.add(str(model))
    return sorted(models)


def model_violations(models: list[str], target: str) -> list[str]:
    """Models other than the target (a `[1m]`-style suffix on the target is allowed)."""
    return [m for m in models if m != target and not m.startswith(f"{target}[")]


def final_text(events: list[dict[str, Any]]) -> str:
    result = result_event(events)
    if result and isinstance(result.get("result"), str):
        return result["result"]
    for event in reversed(events):
        if event.get("type") == "assistant" and not event.get("parent_tool_use_id"):
            content = (event.get("message") or {}).get("content") or []
            texts = [
                b.get("text", "")
                for b in content
                if isinstance(b, dict) and b.get("type") == "text"
            ]
            if texts:
                return "\n".join(texts)
    return ""


# --- process ------------------------------------------------------------------


@dataclass
class RunResult:
    command: list[str]
    cwd: Path
    lines: list[str] = field(default_factory=list)
    returncode: int | None = None
    stopped_early: bool = False
    timed_out: bool = False
    wall_ms: int = 0
    stderr: str = ""

    @property
    def events(self) -> list[dict[str, Any]]:
        return parse_stream(self.lines)


def _kill(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
        process.wait(timeout=5)
    except (ProcessLookupError, subprocess.TimeoutExpired):
        with contextlib.suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGKILL)


def run_claude(
    command: list[str],
    cwd: Path,
    env: dict[str, str],
    timeout: float,
    stop_at_decisive_tool: bool = False,
) -> RunResult:
    """Run one session, streaming stdout; optionally stop at the first decisive
    tool call (see `tool_prefix`)."""
    run = RunResult(command=command, cwd=cwd)
    started = time.monotonic()
    with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as stderr:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=stderr,
            text=True,
            start_new_session=True,
        )
        stop = threading.Event()
        calls: list[dict[str, Any]] = []

        def reader() -> None:
            assert process.stdout is not None
            for line in process.stdout:
                run.lines.append(line)
                if stop_at_decisive_tool and line.startswith("{"):
                    calls.extend(e for e in parse_stream([line]) if tool_uses(e))
                    if calls and tool_prefix(calls)[1] is not None:
                        run.stopped_early = True
                        stop.set()
                        return
            stop.set()

        thread = threading.Thread(target=reader, daemon=True)
        thread.start()
        if not stop.wait(timeout):
            run.timed_out = True
        _kill(process)
        thread.join(timeout=5)
        run.returncode = process.wait()
        if process.stdout is not None:
            process.stdout.close()
        stderr.seek(0)
        run.stderr = stderr.read()[-4000:]
    run.wall_ms = int((time.monotonic() - started) * 1000)
    return run


def preflight(
    project: Path,
    settings_path: Path,
    settings: dict[str, Any],
    expected: set[str],
    model: str,
    effort: str,
) -> dict[str, Any]:
    """Prove isolation with the local `/cost` command (no model call).

    Skills or plugins that still load are switched off and checked once more;
    anything still loaded after that, a missing expected skill, or a connected
    MCP server fails the run.
    """
    for attempt in (1, 2):
        write_json(settings_path, settings)
        command = claude_command(
            "/cost",
            model=model,
            effort=effort,
            settings=settings_path,
            permission_mode="dontAsk",
        )
        run = run_claude(command, project, child_env(model), timeout=120)
        init = init_event(run.events)
        if init is None:
            raise IsolationError(
                f"preflight produced no init event (exit {run.returncode}): {run.stderr.strip()}"
            )
        usage = stream_usage(run.events)
        if usage["total_tokens"]:
            raise IsolationError(
                f"preflight unexpectedly used {usage['total_tokens']} tokens"
            )
        loaded = set(init.get("skills") or [])
        plugins = [p.get("source") or p.get("name") for p in init.get("plugins") or []]
        extra = sorted(loaded - expected)
        if (extra or plugins) and attempt == 1:
            settings["skillOverrides"].update(dict.fromkeys(extra, "off"))
            settings["enabledPlugins"].update(dict.fromkeys(plugins, False))
            continue
        missing = sorted(expected - loaded)
        mcp = [s.get("name") for s in init.get("mcp_servers") or []]
        problems = []
        if extra:
            problems.append(f"unexpected skills still load: {', '.join(extra)}")
        if plugins:
            problems.append(f"plugins still load: {', '.join(map(str, plugins))}")
        if missing:
            problems.append(f"expected skills did not load: {', '.join(missing)}")
        if mcp:
            problems.append(f"MCP servers still connect: {', '.join(map(str, mcp))}")
        if problems:
            raise IsolationError("; ".join(problems))
        return {
            "skills": sorted(loaded),
            "plugins": plugins,
            "mcp_servers": mcp,
            "model": init.get("model"),
            "permission_mode": init.get("permissionMode"),
            "claude_code_version": init.get("claude_code_version"),
            "tools": init.get("tools"),
            "agents": init.get("agents"),
            "memory_paths": init.get("memory_paths"),
        }
    raise AssertionError("unreachable")


def isolation_record(
    settings: dict[str, Any], preflights: dict[str, Any], project_dirs: str
) -> dict[str, Any]:
    user_claude_md = Path.home() / ".claude" / "CLAUDE.md"
    user_settings_path = Path.home() / ".claude" / "settings.json"
    user_settings = (
        read_json(user_settings_path) if user_settings_path.is_file() else {}
    )
    return {
        "settings": settings,
        "flags": [
            "--strict-mcp-config",
            "--no-session-persistence",
            "--permission-prompts none",
        ],
        "project_dirs": project_dirs,
        "preflight": preflights,
        "not_isolated": {
            "user_claude_md": str(user_claude_md) if user_claude_md.is_file() else None,
            "user_settings": str(user_settings_path) if user_settings else None,
            "user_settings_env_keys": sorted((user_settings.get("env") or {}).keys()),
            "user_settings_permissions": bool(user_settings.get("permissions")),
            "note": (
                "User-level CLAUDE.md still loads, and user settings.json still applies "
                "(its env, which can add tools such as the Task* todo tools, and its "
                "permission rules); --settings overrides only the keys it sets. --bare "
                "would skip these but requires ANTHROPIC_API_KEY. The preflight entries "
                "list the tools and agents each session sees."
            ),
        },
    }


def git_state(path: Path) -> dict[str, Any] | None:
    """HEAD and dirty-path count for a catalog inside this repository, else None."""
    if not path.resolve().is_relative_to(REPO_ROOT):
        return None

    def git(*args: str) -> str:
        done = subprocess.run(
            ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=False
        )
        return done.stdout.strip()

    return {
        "head": git("rev-parse", "HEAD"),
        "dirty_paths": len(git("status", "--porcelain", "--", str(path)).splitlines()),
    }
