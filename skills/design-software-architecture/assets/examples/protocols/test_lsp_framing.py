import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lsp_framing import Reader, character_offset, encode


class FramingTests(unittest.TestCase):
    def test_length_counts_bytes_not_characters(self):
        frame = encode({"jsonrpc": "2.0", "method": "log", "params": {"t": "é😀"}})
        header, body = frame.split(b"\r\n\r\n", 1)
        self.assertEqual(int(header.split(b": ")[1]), len(body))
        self.assertGreater(len(body), len(body.decode("utf-8")))

    def test_split_and_merged_reads(self):
        a = encode({"id": 1, "result": "é"})
        b = encode({"id": 2, "result": None})
        stream = a + b
        reader = Reader()
        got = []
        for i in range(0, len(stream), 7):  # 7-byte chunks cut frames anywhere
            got += reader.feed(stream[i : i + 7])
        self.assertEqual([m["id"] for m in got], [1, 2])
        self.assertEqual(Reader().feed(stream)[1]["id"], 2)  # two in one read

    def test_position_units_differ_after_an_emoji(self):
        line = "a😀b"
        self.assertEqual(character_offset(line, 2, "utf-16"), 3)
        self.assertEqual(character_offset(line, 2, "utf-8"), 5)
        self.assertEqual(character_offset(line, 2, "utf-32"), 2)


if __name__ == "__main__":
    unittest.main()
