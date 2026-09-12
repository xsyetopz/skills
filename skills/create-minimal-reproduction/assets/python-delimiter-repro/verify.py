"""Verify that the bundled reproduction produces its documented failure."""

import subprocess
import sys
from pathlib import Path

# Arrange
reproducer = Path(__file__).with_name("repro.py")

# Act
result = subprocess.run(
    [sys.executable, str(reproducer)], capture_output=True, text=True, check=False
)

# Assert
assert result.returncode != 0
assert "ValueError: too many values to unpack" in result.stderr
