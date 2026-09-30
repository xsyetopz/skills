def sales_report(rows):
    total = 0
    lines = []
    for row in rows:
        total += row["amount"]
        lines.append(f"{row['day']}: {row['amount']:.2f}")
    lines.append(f"total: {total:.2f}")
    return "\n".join(lines)
