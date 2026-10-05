export function dueDate(issuedAt, days) {
	return new Date(issuedAt + days * 86_400_000).toISOString().slice(0, 10);
}

export function isOverdue(invoice, now) {
	return !invoice.paid && Date.parse(invoice.due) < now;
}

export function notifyOverdue(invoices, now, send) {
	const overdue = invoices.filter((inv) => isOverdue(inv, now));
	for (const inv of overdue) send(inv.id);
	return overdue.length;
}
