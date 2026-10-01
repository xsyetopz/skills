"""Project test runner: python3 scripts/run_tests.py [-k EXPR] [PATH ...]

-k selects tests whose name matches a boolean expression over words, as in
pytest: `slow and not db`, `parse or render`. PATHs limit the run to those
test files. Prints the filter and the selected test names.
"""
import argparse
import re
import sys
import unittest
from pathlib import Path


def matches(expr, name):
    tokens = re.findall(r"\w+|\(|\)", expr)
    if not tokens:
        return True
    pos = 0

    def peek():
        return tokens[pos] if pos < len(tokens) else None

    def take(expected=None):
        nonlocal pos
        token = peek()
        if token is None or (expected and token != expected):
            raise SyntaxError(expr)
        pos += 1
        return token

    def disjunction():
        result = conjunction()
        while peek() == "or":
            take()
            result = conjunction() or result
        return result

    def conjunction():
        result = negation()
        while peek() == "and":
            take()
            result = negation() and result
        return result

    def negation():
        if peek() == "not":
            take()
            return not negation()
        if peek() == "(":
            take()
            result = disjunction()
            take(")")
            return result
        word = take()
        if word in ("and", "or", ")"):
            raise SyntaxError(expr)
        return word in name

    try:
        result = disjunction()
        if peek() is not None:
            raise SyntaxError(expr)
        return result
    except SyntaxError:
        return expr in name


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-k", dest="expr")
    parser.add_argument("paths", nargs="*")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(root))
    for p in args.paths:
        if not (root / p).is_file():
            print(f"error: no such test file: {p}", file=sys.stderr)
            return 4
    loader = unittest.TestLoader()
    suite = loader.discover(str(root / "tests"), top_level_dir=str(root))
    print(f"filter: {args.expr}")
    selected = []
    def walk(s):
        for t in s:
            if isinstance(t, unittest.TestSuite):
                walk(t)
            else:
                file = "tests/" + t.__class__.__module__.split(".")[-1] + ".py"
                if args.paths and file not in args.paths:
                    continue
                if args.expr and not matches(args.expr, t.id().split(".")[-1]):
                    continue
                selected.append(t)
    walk(suite)
    for t in selected:
        print("selected:", t.id())
    if not selected:
        print("no tests selected")
        return 5
    result = unittest.TextTestRunner(verbosity=0).run(unittest.TestSuite(selected))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
