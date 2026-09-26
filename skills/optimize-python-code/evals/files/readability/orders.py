def summarize(orders):
    result = {}
    for o in orders:
        if o.get("status") not in ("paid", "shipped", "refunded"):
            continue
        c = o.get("customer", "").strip().lower()
        if not c:
            c = "unknown"
        if c not in result:
            result[c] = {"count": 0, "total": 0, "refunds": 0, "items": 0, "last": None}
        r = result[c]
        amt = 0
        for it in o.get("items", []):
            q = it.get("qty", 1)
            if q < 0:
                raise ValueError("negative quantity in order %s" % o.get("id"))
            p = it.get("price_cents", 0)
            d = it.get("discount_pct", 0)
            if d:
                p = p - (p * d) // 100
            amt = amt + p * q
            r["items"] = r["items"] + q
        if o["status"] == "refunded":
            r["refunds"] = r["refunds"] + 1
            r["total"] = r["total"] - amt
        else:
            r["count"] = r["count"] + 1
            r["total"] = r["total"] + amt
        ts = o.get("ts")
        if ts is not None and (r["last"] is None or ts > r["last"]):
            r["last"] = ts
    out = []
    for k in sorted(result):
        v = result[k]
        out.append((k, v["count"], v["total"], v["refunds"], v["items"], v["last"]))
    return out
