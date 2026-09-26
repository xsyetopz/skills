import sys


def summarize(words):
    r = {}
    for w in words:
        if w:
            w2 = w.strip().lower()
            if w2:
                if w2 in r:
                    r[w2] = r[w2] + 1
                else:
                    r[w2] = 1
    out = []
    for k in sorted(r, key=lambda k: (-r[k], k)):
        out.append(k + ":" + str(r[k]))
    return ", ".join(out)


if sys.version_info >= (3, 10):
    def pairs(xs):
        from itertools import pairwise
        return list(pairwise(xs))
else:
    def pairs(xs):
        return list(zip(xs, xs[1:]))
