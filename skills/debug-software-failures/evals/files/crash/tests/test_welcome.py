import json
import tempfile
import unittest
from pathlib import Path

from users import UserStore
from welcome import send_welcome


class WelcomeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        path = Path(self.tmp.name) / "users.json"
        path.write_text(json.dumps([{"id": 1, "name": "Ada", "email": "ada@example.invalid"}]))
        self.store = UserStore(path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_known_user(self):
        self.assertEqual(send_welcome(self.store, 1), "To: ada@example.invalid\nSubject: Welcome, Ada!")

    def test_unknown_user_is_reported_by_the_store(self):
        with self.assertRaises(LookupError):
            self.store.find_user(999)

    def test_unknown_user_gets_no_welcome(self):
        with self.assertRaises(LookupError):
            send_welcome(self.store, 999)


if __name__ == "__main__":
    unittest.main()
