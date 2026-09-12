"""Parse checked-in configuration assets using standard or installed parsers."""

import json
import plistlib
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import tomllib
import yaml


def main() -> int:
    errors: list[str] = []
    for path in Path("skills").rglob("*"):
        if not path.is_file():
            continue
        try:
            if path.suffix == ".json":
                json.loads(path.read_text())
            elif path.suffix in {".yaml", ".yml"}:
                yaml.safe_load(path.read_text())
            elif path.suffix == ".toml":
                tomllib.loads(path.read_text())
            elif path.suffix == ".xml":
                ET.parse(path)
            elif path.suffix == ".plist":
                plistlib.loads(path.read_bytes())
            elif path.suffix == ".py" and not path.name.startswith("test_"):
                compile(path.read_text(), str(path), "exec")
            elif path.suffix == ".sh":
                result = subprocess.run(
                    ["bash", "-n", str(path)],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if result.returncode:
                    raise ValueError(result.stderr.strip())
        except (
            OSError,
            SyntaxError,
            UnicodeError,
            ValueError,
            ET.ParseError,
            yaml.YAMLError,
        ) as error:
            errors.append(f"{path}: {error}")
    print("\n".join(errors), file=sys.stderr)
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
