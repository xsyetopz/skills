import argparse
import sys
from pathlib import Path

from users import UserStore
from welcome import send_welcome


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--user", type=int, required=True)
    args = parser.parse_args(argv)
    store = UserStore(Path(__file__).with_name("users.json"))
    print(send_welcome(store, args.user))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
