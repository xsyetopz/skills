"""Pure conversion between integer row ids and base62 short codes."""

ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


def encode(number: int) -> str:
    if number < 0:
        raise ValueError("ids are non-negative")
    digits = []
    while True:
        number, rest = divmod(number, len(ALPHABET))
        digits.append(ALPHABET[rest])
        if number == 0:
            return "".join(reversed(digits))


def decode(code: str) -> int:
    number = 0
    for char in code:
        index = ALPHABET.find(char)
        if index < 0:
            raise ValueError(f"not a short code: {code!r}")
        number = number * len(ALPHABET) + index
    return number
