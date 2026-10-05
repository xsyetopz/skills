import warnings


def area(shape, units):
    width, height = shape
    square_metres = width * height
    if units == "m2":
        return square_metres
    if units == "ha":
        return square_metres / 10_000
    raise ValueError(f"unknown units: {units}")


def legacy_area(shape):
    warnings.warn(
        "legacy_area() is deprecated; use area(shape, units='ha')",
        DeprecationWarning,
        stacklevel=2,
    )
    return area(shape, "ha")
