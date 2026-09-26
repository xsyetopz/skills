"""Exploit-condition and fix tests for files.py (stdlib only, POSIX).

Run: python3 test_files.py
All files live in a TemporaryDirectory; the "secret" is synthetic.
"""

from __future__ import annotations

import io
import os
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import files


class Sandbox(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.tmp = Path(directory.name)
        self.root = self.tmp / "public"
        self.root.mkdir()
        (self.root / "readme.txt").write_bytes(b"hello")
        self.secret = self.tmp / "secret.txt"
        self.secret.write_bytes(b"SYNTHETIC-SECRET")


class PathTraversal(Sandbox):
    def test_dot_dot_and_absolute_names_escape(self) -> None:
        self.assertEqual(
            files.vulnerable_read(self.root, "../secret.txt"), b"SYNTHETIC-SECRET"
        )
        self.assertEqual(
            files.vulnerable_read(self.root, str(self.secret)), b"SYNTHETIC-SECRET"
        )

    def test_resolved_containment_blocks_escape(self) -> None:
        for name in ("../secret.txt", str(self.secret), "a/../../secret.txt"):
            with self.subTest(name=name), self.assertRaises(PermissionError):
                files.fixed_read(self.root, name)
        self.assertEqual(files.fixed_read(self.root, "readme.txt"), b"hello")

    def test_symlink_inside_root_is_resolved_before_the_check(self) -> None:
        (self.root / "link").symlink_to(self.secret)
        with self.assertRaises(PermissionError):
            files.fixed_read(self.root, "link")

    def test_prefix_string_check_is_not_containment(self) -> None:
        # "/tmp/x/public_evil" starts with "/tmp/x/public" as a string.
        sibling = self.tmp / "public_evil"
        sibling.mkdir()
        self.assertTrue(str(sibling).startswith(str(self.root)))
        self.assertFalse(sibling.resolve().is_relative_to(self.root.resolve()))


class ArchiveExtraction(Sandbox):
    def make_archive(self) -> Path:
        archive = self.tmp / "upload.tar"
        with tarfile.open(archive, "w") as tar:
            info = tarfile.TarInfo("../escaped.txt")
            payload = b"written outside dest"
            info.size = len(payload)
            tar.addfile(info, io.BytesIO(payload))
        return archive

    def test_fully_trusted_writes_outside_destination(self) -> None:
        dest = self.tmp / "dest"
        dest.mkdir()
        files.vulnerable_extract(self.make_archive(), dest)
        self.assertTrue((self.tmp / "escaped.txt").exists())

    def test_data_filter_refuses_the_member(self) -> None:
        dest = self.tmp / "dest"
        dest.mkdir()
        with self.assertRaises(tarfile.OutsideDestinationError):
            files.fixed_extract(self.make_archive(), dest)
        self.assertFalse((self.tmp / "escaped.txt").exists())


@unittest.skipUnless(hasattr(os, "O_NOFOLLOW"), "needs O_NOFOLLOW (POSIX)")
class CheckThenUse(Sandbox):
    def setUp(self) -> None:
        super().setUp()
        self.upload = self.root / "upload.bin"
        self.upload.write_bytes(b"user data")

    def swap_to_symlink(self, path: Path, target: Path) -> None:
        path.unlink()
        path.symlink_to(target)

    def test_symlink_swap_between_check_and_open(self) -> None:
        data = files.vulnerable_read_upload(
            self.upload, lambda: self.swap_to_symlink(self.upload, self.secret)
        )
        self.assertEqual(data, b"SYNTHETIC-SECRET")

    def test_nofollow_open_refuses_the_swapped_link(self) -> None:
        with self.assertRaises(OSError):
            files.fixed_read_upload(
                self.upload,
                lambda: self.swap_to_symlink(self.upload, self.secret),
            )
        self.assertEqual(files.fixed_read_upload(self.root / "readme.txt"), b"hello")

    def test_planted_symlink_truncates_target(self) -> None:
        report = self.root / "report.txt"
        files.vulnerable_create_report(
            report, "overwritten", lambda: report.symlink_to(self.secret)
        )
        self.assertEqual(self.secret.read_text(), "overwritten")

    def test_exclusive_create_refuses_planted_symlink(self) -> None:
        report = self.root / "report.txt"
        with self.assertRaises(FileExistsError):
            files.fixed_create_report(
                report, "overwritten", lambda: report.symlink_to(self.secret)
            )
        self.assertEqual(self.secret.read_bytes(), b"SYNTHETIC-SECRET")


if __name__ == "__main__":
    unittest.main()
