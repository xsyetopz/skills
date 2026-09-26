import json, sys


def log(**fields):
    sys.stdout.write(json.dumps(fields) + "\n")
