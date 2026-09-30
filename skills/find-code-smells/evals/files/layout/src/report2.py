def sales_report(rows, currency):
    total = 0
    lines = []
    for row in rows:
        total += row["amount"]
        lines.append(f"{row['day']}: {row['amount']:.2f} {currency}")
    lines.append(f"total: {total:.2f} {currency}")
    return "\n".join(lines)
