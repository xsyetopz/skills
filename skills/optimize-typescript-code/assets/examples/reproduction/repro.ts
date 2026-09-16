let completed = 0;
[1, 2].forEach(async () => {
	await Promise.resolve();
	completed++;
});
console.log(`actual immediate completed=${completed}`);
console.log("expected completed=2 before return");
if (completed !== 0) process.exit(1);
