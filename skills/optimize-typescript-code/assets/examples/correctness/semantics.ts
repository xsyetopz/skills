// Node 22.6+ with --experimental-strip-types, or Bun; no runtime-specific core APIs.
async function contract(bad: boolean, topic: number): Promise<boolean> {
    switch (topic) {
    case 1: { // Membership uses SameValueZero: NaN is a member of [NaN].
        const values = [NaN];
        return bad ? values.indexOf(NaN) >= 0 : values.includes(NaN);
    }
    case 2: { // Produce dense output, not holes that map skips.
        const input = new Array<number>(3); input[2] = 1;
        const output = bad ? input.map(v => v ?? 0) : Array.from(input, v => v ?? 0);
        return output.length === 3 && 0 in output && output[0] === 0;
    }
    case 3: { // Return only when all required asynchronous work has finished.
        let completed = 0;
        const work = async () => { await Promise.resolve(); completed++; };
        if (bad) [1,2].forEach(async () => { await work(); });
        else await Promise.all([1,2].map(work));
        const pass = completed === 2;
        await Promise.resolve(); await Promise.resolve(); // Drain the mutant's work.
        return pass;
    }
    case 4: { // The specified concurrency bound is two.
        let active=0, peak=0;
        const work=async () => { active++; peak=Math.max(peak,active); await Promise.resolve(); active--; };
        if (bad) await Promise.all([1,2,3].map(work));
        else { await Promise.all([1,2].map(work)); await work(); }
        return peak <= 2 && active === 0;
    }
    case 5: { // Clone JS data without erasing undefined properties or NaN.
        const input={missing: undefined, value:NaN};
        const output=bad ? JSON.parse(JSON.stringify(input)) : structuredClone(input);
        return Object.hasOwn(output,'missing') && Number.isNaN(output.value);
    }
    case 6: { // Copy, rather than transfer, when the sender must retain ownership.
        const input=new ArrayBuffer(4);
        const output=bad ? structuredClone(input,{transfer:[input]}) : structuredClone(input);
        return input.byteLength === 4 && output.byteLength === 4;
    }
    case 7: { // Rows own independent mutable cells.
        const rows=bad ? Array(2).fill({value:0}) : [0,0].map(value => ({value}));
        rows[0].value=1;
        return rows[1].value === 0;
    }
    case 8: { // A TypeScript cast is not validation of a wire value.
        const value: unknown=JSON.parse('{"id":"not-a-number"}');
        const accepted=bad ? true : (typeof value==='object' && value!==null && 'id' in value &&
                                     typeof value.id==='number' && Number.isFinite(value.id));
        return !accepted;
    }
    default: throw new Error('topic must be 1..8');
    }
}
const [mode,rawTopic]=process.argv.slice(2);
if (mode!=='red' && mode!=='green') throw new Error('usage: red|green TOPIC');
const topic=Number(rawTopic);
const pass=await contract(mode==='red',topic);
console.log(`CONTRACT topic ${topic}: ${pass?'PASS':'FAIL'}`);
process.exit(pass?0:1);
export {};
