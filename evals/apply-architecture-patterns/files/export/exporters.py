import json


def export_json(rows):
    return json.dumps(rows, indent=2)
