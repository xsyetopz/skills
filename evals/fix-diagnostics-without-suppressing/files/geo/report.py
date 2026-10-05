from shapes import legacy_area


def total_ha(plots):
    return sum(legacy_area(plot) for plot in plots)


def line(name, plots):
    return f"{name}: {total_ha(plots):.2f} ha"
