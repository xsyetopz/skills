"""Split one CSV line into fields."""


def parse_csv_line(line: str) -> list[str]:
    """Split `line` into fields.

    Commas separate fields. A field wrapped in double quotes may contain
    commas, and "" inside quotes is a literal quote. Empty fields are kept,
    so a line with N commas outside quotes always has N + 1 fields.
    """
    fields: list[str] = []
    field: list[str] = []
    quoted = False
    i = 0
    while i < len(line):
        ch = line[i]
        if quoted:
            if ch == '"':
                if i + 1 < len(line) and line[i + 1] == '"':
                    field.append('"')
                    i += 1
                else:
                    quoted = False
            else:
                field.append(ch)
        elif ch == '"':
            quoted = True
        elif ch == ",":
            if field:
                fields.append("".join(field))
            field = []
        else:
            field.append(ch)
        i += 1
    if field:
        fields.append("".join(field))
    return fields
