import type { Invoice } from "../models/invoice";

export async function loadInvoices(): Promise<Invoice[]> {
	const response = await fetch("/api/invoices");
	return (await response.json()) as Invoice[];
}
