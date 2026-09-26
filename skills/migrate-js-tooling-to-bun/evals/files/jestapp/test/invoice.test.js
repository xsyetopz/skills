import { dueDate, isOverdue, notifyOverdue } from "../src/invoice.js";

describe("dueDate", () => {
	it("adds days", () => {
		expect(dueDate(globalThis.FIXED_NOW, 30)).toBe("2026-02-14");
	});
});

describe("isOverdue", () => {
	it("ignores paid invoices", () => {
		expect(isOverdue({ paid: true, due: "2026-01-01" }, globalThis.FIXED_NOW)).toBe(false);
	});
	it("flags unpaid past-due invoices", () => {
		expect(isOverdue({ paid: false, due: "2026-01-01" }, globalThis.FIXED_NOW)).toBe(true);
	});
});

describe("notifyOverdue", () => {
	it("sends one notice per overdue invoice", () => {
		const send = jest.fn();
		const n = notifyOverdue(
			[
				{ id: "a", paid: false, due: "2026-01-01" },
				{ id: "b", paid: true, due: "2026-01-01" },
				{ id: "c", paid: false, due: "2026-03-01" },
			],
			globalThis.FIXED_NOW,
			send,
		);
		expect(n).toBe(1);
		expect(send).toHaveBeenCalledTimes(1);
		expect(send).toHaveBeenCalledWith("a");
	});
});
