export function baselineAppend(values) {
    let result = [];
    for (const value of values)
        result = result.concat([value]);
    return result;
}
export function candidateAppend(values) {
    const result = [];
    for (const value of values)
        result.push(value);
    return result;
}
export function baselineCounts(values) {
    const result = [];
    for (const value of values) {
        let found = false;
        for (const item of result) {
            if (item[0] === value) {
                item[1] += 1;
                found = true;
                break;
            }
        }
        if (!found)
            result.push([value, 1]);
    }
    return result;
}
export function candidateCounts(values) {
    const counts = new Map();
    for (const value of values) {
        const previous = counts.get(value);
        counts.set(value, previous === undefined ? 1 : previous + 1);
    }
    return Array.from(counts.entries());
}
export function baselineMembership(values, queries) {
    return queries.map((query) => values.indexOf(query) !== -1);
}
export function candidateMembership(values, queries) {
    const members = new Set(values);
    return queries.map((query) => members.has(query));
}
export function baselineJoin(values) {
    return values.reduce((prefix, value) => prefix + value, "");
}
export function candidateJoin(values) {
    return values.join("");
}
export function baselineSum(values) {
    return values
        .filter((value) => value % 2 === 0)
        .map((value) => value * value)
        .reduce((sum, value) => sum + value, 0);
}
export function candidateSum(values) {
    let sum = 0;
    for (const value of values)
        if (value % 2 === 0)
            sum += value * value;
    return sum;
}
export function baselineDelimiter(values) {
    return values.map((value) => value.split(":").length > 1);
}
export function candidateDelimiter(values) {
    return values.map((value) => value.indexOf(":") !== -1);
}
export function baselineChangingShapes(values) {
    const records = [];
    for (let index = 0; index < values.length; index++) {
        const record = {};
        if (index % 2 === 0) {
            record.x = values[index];
            record.y = index;
        }
        else {
            record.y = index;
            record.x = values[index];
        }
        records.push(record);
    }
    let sum = 0;
    for (const record of records)
        sum += record.x + record.y;
    return sum;
}
export function candidateStableShapes(values) {
    const records = values.map((value, index) => ({ x: value, y: index }));
    let sum = 0;
    for (const record of records)
        sum += record.x + record.y;
    return sum;
}
export function baselineObjectRecords(values) {
    const records = values.map((value, index) => ({ x: value, y: index }));
    let sum = 0;
    for (const record of records)
        sum += record.x * 2 + record.y;
    return sum;
}
export function candidateTypedStorage(values) {
    const x = new Float64Array(values);
    const y = new Float64Array(values.length);
    for (let index = 0; index < y.length; index++)
        y[index] = index;
    let sum = 0;
    for (let index = 0; index < x.length; index++)
        sum += x[index] * 2 + y[index];
    return sum;
}
export function run(variant, which, size) {
    if (variant !== "baseline" && variant !== "candidate")
        throw new Error("bad variant");
    if (!Number.isInteger(size) || size < 0 || size > 100000)
        throw new Error("bad size");
    const values = [];
    for (let i = 0; i < size; i++)
        values.push((i % 31) - 15);
    const strings = values.map(String);
    const candidate = variant === "candidate";
    switch (which) {
        case 1:
            return candidate ? candidateAppend(values) : baselineAppend(values);
        case 2:
            return candidate ? candidateCounts(strings) : baselineCounts(strings);
        case 3:
            return candidate
                ? candidateMembership(strings, strings)
                : baselineMembership(strings, strings);
        case 4:
            return candidate ? candidateJoin(strings) : baselineJoin(strings);
        case 5:
            return candidate ? candidateSum(values) : baselineSum(values);
        case 6:
            return candidate
                ? candidateDelimiter(strings)
                : baselineDelimiter(strings);
        case 7:
            return candidate
                ? candidateStableShapes(values)
                : baselineChangingShapes(values);
        case 8:
            return candidate
                ? candidateTypedStorage(values)
                : baselineObjectRecords(values);
        default:
            throw new Error("case must be 1..8");
    }
}
function equal(a, b) {
    if (JSON.stringify(a) !== JSON.stringify(b))
        throw new Error("not equivalent");
}
export function verify() {
    let checks = 0;
    for (let length = 0; length <= 5; length++) {
        for (let code = 0; code < 3 ** length; code++) {
            let rest = code;
            const numbers = [];
            for (let i = 0; i < length; i++) {
                numbers.push((rest % 3) - 1);
                rest = Math.floor(rest / 3);
            }
            const strings = numbers.map(String);
            const before = JSON.stringify(numbers);
            equal(baselineAppend(numbers), candidateAppend(numbers));
            equal(baselineCounts(strings), candidateCounts(strings));
            equal(baselineMembership(strings, ["0", "9"]), candidateMembership(strings, ["0", "9"]));
            equal(baselineJoin(strings), candidateJoin(strings));
            equal(baselineSum(numbers), candidateSum(numbers));
            equal(baselineDelimiter(strings), candidateDelimiter(strings));
            equal(baselineChangingShapes(numbers), candidateStableShapes(numbers));
            equal(baselineObjectRecords(numbers), candidateTypedStorage(numbers));
            equal(JSON.stringify(numbers), before);
            checks += 9;
        }
    }
    equal(candidateCounts(["__proto__", "é", "__proto__", "e\u0301"]), [
        ["__proto__", 2],
        ["é", 1],
        ["e\u0301", 1],
    ]);
    for (const fn of [baselineJoin, candidateJoin])
        equal(fn(["a", "", "é", "🙂", "\0"]), "aé🙂\0");
    for (const fn of [baselineDelimiter, candidateDelimiter])
        equal(fn(["", ":", "a:b", "：", "🙂"]), [false, true, true, false, false]);
    for (const fn of [baselineSum, candidateSum])
        equal(fn([-3, 2, 2, 0, 5]), 8);
    for (const fn of [baselineMembership, candidateMembership])
        equal(fn(["a", "a"], ["a", "b"]), [true, false]);
    // Rejected substitution outside the string-only contract: indexOf and Set differ for NaN.
    equal([NaN].indexOf(NaN), -1);
    equal(new Set([NaN]).has(NaN), true);
    // Sharing a typed-array view is not an owning copy.
    const owner = new Uint8Array([1, 2]);
    const view = owner.subarray(0, 1);
    const copy = owner.slice(0, 1);
    owner[0] = 9;
    equal(view[0], 9);
    equal(copy[0], 1);
    return checks + 13;
}
