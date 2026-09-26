import unittest

import notes


class NotesTest(unittest.TestCase):
    def setUp(self) -> None:
        notes.NOTES.clear()

    def test_add_and_list(self) -> None:
        self.assertEqual(notes.add_note("ann", "hi"), 1)
        self.assertEqual(notes.list_notes("ann"), ["hi"])


if __name__ == "__main__":
    unittest.main()
