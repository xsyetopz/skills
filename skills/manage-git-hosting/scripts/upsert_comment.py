#!/usr/bin/env python3
"""Create or update one bot comment on a GitHub issue or pull request.

The comment body carries a hidden marker (<!-- upsert:KEY -->). If a
comment with that marker already exists, it is edited in place;
otherwise one is created. Rerunning after a timeout or retry therefore
never posts a duplicate. Reads all comment pages (`gh api --paginate`).

Usage: upsert_comment.py REPO NUMBER KEY BODY_FILE [--apply] [--json]
Without --apply, prints what it would do and exits 0.
Exit status: 0 success, 1 a gh call failed, 2 bad input.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

EPILOG = """\
Exit status:
  0  success: planned, already up to date, or created/updated
  1  a gh call failed (or gh is not installed)
  2  bad input: BODY_FILE cannot be read

Output: "plan create comment on #N" / "plan update comment ID" without
--apply, "done ...: URL" with it, or "comment ID already up to date".
--json prints {"action": "create"|"update"|"none", "comment_id",
"applied", "url"}.

Examples:
  python3 scripts/upsert_comment.py acme/app 42 coverage report.md
  python3 scripts/upsert_comment.py acme/app 42 coverage report.md --apply
"""


def gh(*args: str, stdin: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["gh", *args], input=stdin, capture_output=True, text=True, check=False
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(__doc__ or "").splitlines()[0],
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("repo", help="OWNER/REPO")
    parser.add_argument("number", type=int, help="issue or pull request number")
    parser.add_argument("key", help="marker key that identifies this bot comment")
    parser.add_argument("body_file", type=Path, help="Markdown body of the comment")
    parser.add_argument(
        "--apply", action="store_true", help="create or edit (default: plan only)"
    )
    parser.add_argument("--json", action="store_true", help="print a JSON report")
    args = parser.parse_args(argv)
    try:
        return upsert(args)
    except FileNotFoundError:
        print(
            "error: gh not found on PATH; install GitHub CLI and run `gh auth login`",
            file=sys.stderr,
        )
        return 1


def upsert(args: argparse.Namespace) -> int:
    def emit(action: str, comment_id: object, applied: bool, url: str | None) -> None:
        report = {
            "action": action,
            "comment_id": comment_id,
            "applied": applied,
            "url": url,
        }
        print(json.dumps(report, indent=2))

    try:
        text = args.body_file.read_text(encoding="utf-8")
    except OSError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    marker = f"<!-- upsert:{args.key} -->"
    body = f"{marker}\n{text}"
    listing = gh(
        "api",
        "--paginate",
        "--slurp",
        f"repos/{args.repo}/issues/{args.number}/comments",
    )
    if listing.returncode != 0:
        print(f"error: {listing.stderr.strip()}", file=sys.stderr)
        return 1
    pages = json.loads(listing.stdout)
    comments = [c for page in pages for c in page]
    existing = [c for c in comments if marker in (c.get("body") or "")]
    if existing and existing[0].get("body") == body:
        if args.json:
            emit("none", existing[0]["id"], False, existing[0].get("html_url"))
        else:
            print(f"comment {existing[0]['id']} already up to date")
        return 0
    payload = json.dumps({"body": body})
    if existing:
        endpoint = f"repos/{args.repo}/issues/comments/{existing[0]['id']}"
        action = ["api", "--method", "PATCH", endpoint, "--input", "-"]
        description = f"update comment {existing[0]['id']}"
    else:
        endpoint = f"repos/{args.repo}/issues/{args.number}/comments"
        action = ["api", "--method", "POST", endpoint, "--input", "-"]
        description = f"create comment on #{args.number}"
    kind = "update" if existing else "create"
    comment_id = existing[0]["id"] if existing else None
    if not args.apply:
        if args.json:
            emit(kind, comment_id, False, None)
        else:
            print(f"plan {description}")
        return 0
    result = gh(*action, stdin=payload)
    if result.returncode != 0:
        print(f"error: {result.stderr.strip()}", file=sys.stderr)
        return 1
    posted = json.loads(result.stdout)
    if args.json:
        emit(kind, posted.get("id", comment_id), True, posted.get("html_url"))
    else:
        print(f"done {description}: {posted.get('html_url', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
