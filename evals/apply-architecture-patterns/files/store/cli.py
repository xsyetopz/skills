"""Phone orders: python3 cli.py 2500x2 1200x1 prints the total in cents."""

import sys

from domain.pricing import order_total


def main(argv):
    items = [tuple(int(part) for part in arg.split("x")) for arg in argv]
    print(order_total(items))


if __name__ == "__main__":
    main(sys.argv[1:])
