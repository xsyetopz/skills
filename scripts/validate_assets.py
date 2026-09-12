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
            match path.suffix:
                case ".json":
                    json.loads(path.read_text())
                case ".yaml" | ".yml":
                    yaml.safe_load(path.read_text())
                case ".toml":
                    tomllib.loads(path.read_text())
                case ".xml":
                    ET.parse(path)
                case ".plist":
                    plistlib.loads(path.read_bytes())
                case ".py" if not path.name.startswith("test_"):
                    compile(path.read_text(), str(path), "exec")
                case ".sh":
                    result = subprocess.run(
                        ["bash", "-n", str(path)],
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    if result.returncode:
                        errors.append(f"{path}: {result.stderr.strip()}")
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
