def badge(count, level):
    return "" if count == 0 else f"E{'99+' if count > 99 else count}" if level == "error" else f"W{'99+' if count > 99 else count}" if level == "warn" else f"{count}"
