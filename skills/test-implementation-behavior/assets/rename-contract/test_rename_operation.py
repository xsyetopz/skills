"""Run with Python 3; observes files, not comments or implementation structure."""

import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from typing import Callable

_module_path = Path(__file__).with_name("rename_operation.py")
_spec = importlib.util.spec_from_file_location("rename_operation", _module_path)
if _spec is None or _spec.loader is None:
    raise RuntimeError(f"cannot load {_module_path}")
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
rename_file: Callable[[Path, Path], Path] = _module.rename_file


def alternative(source: Path, destination: Path) -> Path:
    """A different implementation of the same stated, non-concurrent contract."""
    if source.parent.resolve() != destination.parent.resolve():
        raise ValueError("source and destination must be siblings")
    if not source.is_file() or source.is_symlink():
        raise FileNotFoundError(source)
    if os.path.lexists(destination):
        raise FileExistsError(destination)
    os.rename(source, destination)
    return destination


def no_op(source: Path, destination: Path) -> Path:
    """Deliberate fault: plausible return value without the required effect."""
    return destination


class RenameContract(unittest.TestCase):
    def check_move(self, operation: Callable[[Path, Path], Path]) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, destination = root / "before.txt", root / "after.txt"
            content = b"unchanged bytes\x00\xff\n"
            source.write_bytes(content)
            result = operation(source, destination)
            self.assertEqual(result, destination)
            self.assertFalse(source.exists(), "source must no longer exist")
            self.assertEqual(destination.read_bytes(), content)
            self.assertEqual(set(root.iterdir()), {destination})

    def test_implementation_and_alternative_satisfy_the_same_contract(self) -> None:
        for operation in (rename_file, alternative):
            with self.subTest(operation=operation.__name__):
                self.check_move(operation)

    def test_same_oracle_rejects_no_effect_despite_plausible_return(self) -> None:
        with self.assertRaisesRegex(AssertionError, "source must no longer exist"):
            self.check_move(no_op)

    def test_existing_destination_is_not_replaced(self) -> None:
        for operation in (rename_file, alternative):
            with (
                self.subTest(operation=operation.__name__),
                tempfile.TemporaryDirectory() as directory,
            ):
                source, destination = Path(directory) / "a", Path(directory) / "b"
                source.write_bytes(b"source")
                destination.write_bytes(b"existing")
                with self.assertRaises(FileExistsError):
                    operation(source, destination)
                self.assertEqual(source.read_bytes(), b"source")
                self.assertEqual(destination.read_bytes(), b"existing")

    def test_missing_source_does_not_create_destination(self) -> None:
        for operation in (rename_file, alternative):
            with (
                self.subTest(operation=operation.__name__),
                tempfile.TemporaryDirectory() as directory,
            ):
                source, destination = Path(directory) / "a", Path(directory) / "b"
                with self.assertRaises(FileNotFoundError):
                    operation(source, destination)
                self.assertEqual(list(Path(directory).iterdir()), [])

    def test_outside_contract_parent_is_rejected_without_moving(self) -> None:
        for operation in (rename_file, alternative):
            with (
                self.subTest(operation=operation.__name__),
                tempfile.TemporaryDirectory() as directory,
            ):
                root = Path(directory)
                sub = root / "sub"
                sub.mkdir()
                source, destination = root / "a", sub / "b"
                source.write_bytes(b"source")
                with self.assertRaises(ValueError):
                    operation(source, destination)
                self.assertEqual(source.read_bytes(), b"source")
                self.assertFalse(destination.exists())


if __name__ == "__main__":
    unittest.main()
