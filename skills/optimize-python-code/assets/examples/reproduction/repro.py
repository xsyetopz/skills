def consume_twice(values):
    return list(values), list(values)


actual = consume_twice(iter([1, 2]))
expected = ([1, 2], [1, 2])
print(f"actual={actual!r}")
print(f"expected={expected!r}")
raise SystemExit(0 if actual != expected else 1)
