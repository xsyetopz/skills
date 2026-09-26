// Target for --trace-opt/--trace-deopt: one call site first sees only small
// integers, then a string. Run: node --trace-deopt deopt.mjs [stable]
function add(a, b) {
	return a + b;
}
const joinText = (a, b) => `${a}${b}`; // strings get their own function

const stable = process.argv[2] === "stable";
let sum = 0;
for (let i = 0; i < 200_000; i++) sum = add(i, 1) | 0;
const text = stable ? joinText("x", "y") : add("x", "y");
for (let i = 0; i < 200_000; i++) sum = add(i, 1) | 0;
console.log(text, sum);
