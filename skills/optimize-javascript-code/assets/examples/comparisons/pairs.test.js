import assert from 'node:assert/strict';
import { test } from 'node:test';
import { run, verify } from './pairs.js';
test('independent fixture oracles and baseline/candidate equivalence', () => {
    assert.ok(verify() > 0);
    for (let which = 1; which <= 8; which++)
        for (const size of [0, 1, 2, 12]) {
            assert.deepEqual(run('candidate', which, size), run('baseline', which, size));
        }
});
