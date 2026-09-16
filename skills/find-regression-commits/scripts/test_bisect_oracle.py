"""Status mapping and actual child invocation tests, not synthetic Git success."""

import contextlib
import io
import sys
import unittest

from bisect_oracle import classify, main


class OracleTests(unittest.TestCase):
    def test_known_status_mapping(self):
        self.assertEqual(classify(0, {1}, {3}), 0)
        self.assertEqual(classify(1, {1}, {3}), 1)
        self.assertEqual(classify(3, {1}, {3}), 125)

    def test_unknown_and_signal_abort(self):
        for code in (-9, -15, 2, 125, 126, 127, 130, 255):
            with self.subTest(code=code):
                self.assertEqual(classify(code, {1}, {3}), 128)

    def test_actual_good_bad_skip_and_unclassified_command(self):
        for code, expected in ((0, 0), (1, 1), (3, 125), (2, 128)):
            with self.subTest(code=code), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(
                    main(
                        [
                            "--skip-exit",
                            "3",
                            "--",
                            sys.executable,
                            "-c",
                            f"raise SystemExit({code})",
                        ]
                    ),
                    expected,
                )

    def test_no_shell_interpolation(self):
        argument = 'space ; $(must-not-run) * "quoted"'
        self.assertEqual(
            main(
                [
                    "--",
                    sys.executable,
                    "-c",
                    "import sys; assert sys.argv[1] == " + repr(argument),
                    argument,
                ]
            ),
            0,
        )

    def test_missing_executable_aborts(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(["--", "/missing/fixture/no-such-program"]), 128)

    def test_timeout_aborts(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(
                main(
                    [
                        "--timeout",
                        ".05",
                        "--",
                        sys.executable,
                        "-c",
                        "import time; time.sleep(5)",
                    ]
                ),
                128,
            )

    def test_conflicting_status_definition_fails(self):
        with (
            contextlib.redirect_stderr(io.StringIO()),
            self.assertRaises(SystemExit) as caught,
        ):
            main(["--bad-exit", "3", "--skip-exit", "3", "--", sys.executable])
        self.assertEqual(caught.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
