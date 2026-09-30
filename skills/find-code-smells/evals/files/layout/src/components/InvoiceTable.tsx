import type { Invoice } from "../models/invoice";
import { formatMoney } from "../utils";

export function InvoiceTable({ invoices }: { invoices: Invoice[] }) {
	return invoices
		.map((i) => `${i.number}: ${formatMoney(i.totalCents)}`)
		.join("\n");
}
