"""Command-line entry point for the `app` tool."""

import argparse

from app.report_engine import ReportEngine


def make_engine(scale: int) -> ReportEngine:
    return ReportEngine(scale)


def cmd_report(args: argparse.Namespace) -> int:
    engine = make_engine(args.scale)
    print(engine.render(range(1, args.count + 1)))
    return 0


def cmd_version(args: argparse.Namespace) -> int:
    print("app 2.3.1")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="app", description="Ops helper.")
    sub = parser.add_subparsers(dest="command", required=True)
    report = sub.add_parser("report", help="print the weighted report")
    report.add_argument("--count", type=int, default=10)
    report.add_argument("--scale", type=int, default=1)
    report.set_defaults(func=cmd_report)
    version = sub.add_parser("version", help="print the version")
    version.set_defaults(func=cmd_version)
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)
