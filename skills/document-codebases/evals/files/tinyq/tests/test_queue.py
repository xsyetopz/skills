import unittest

from tinyq import Queue


class QueueTest(unittest.TestCase):
    def test_fifo(self) -> None:
        q = Queue()
        q.put("a")
        q.put("b")
        self.assertEqual([q.get(), q.get(), q.get()], ["a", "b", None])


if __name__ == "__main__":
    unittest.main()
