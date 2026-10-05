import re

NOT_WORD = re.compile("[^\w\s-]")
SEPARATORS = re.compile("[\s_-]+")


def slugify(text):
    text = NOT_WORD.sub("", text.lower()).strip()
    return SEPARATORS.sub("-", text)
