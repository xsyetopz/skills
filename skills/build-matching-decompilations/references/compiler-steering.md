# Compiler steering

## Contents

- [How to use these techniques](#how-to-use-these-techniques)
- [Split expressions, add temporaries](#split-expressions-add-temporaries)
- [Reorder reads and writes](#reorder-reads-and-writes)
- [Change the branch shape](#change-the-branch-shape)
- [Declaration order and types](#declaration-order-and-types)
- [Keep original behavior](#keep-original-behavior)
- [Grounding](#grounding)

## How to use these techniques

When a function compiles to nearly the right code, the remaining
differences usually come from choices the compiler makes from the shape of
the source: which operands it groups, which value it loads first, which
block it places after a branch, and which register or stack slot it gives
each variable. The same behavior can be written in several shapes, and
the original programmer wrote one of them.

The loop, for one function:

1. Build with the pinned toolchain and diff against the target (objdiff
   or the project's verifier; use a decomp.me scratch only when the user
   supplies one, because a scratch publishes the target assembly).
1. Name the first difference: a swapped register, a load in a different
   place, an inverted branch, a different stack offset.
1. Pick the one technique below that addresses that kind of difference
   and make one change.
1. Rebuild, diff, and log the attempt with the differing byte count,
   whether it improved or not.
1. Revert a change that made the diff worse, unless it fixed a
   difference earlier in the function; log the revert too.

Every technique here must leave behavior unchanged. If the only shape that
matches changes what the function computes, the reading of the target is
wrong; go back to the disassembly.

## Split expressions, add temporaries

Symptom: the same operations appear in a different order, or an
intermediate result lands in a different register.

Compilers may regroup associative integer arithmetic and reuse common
subexpressions. Writing the intermediate result into a named local, or
splitting one expression into two statements, often changes the grouping
the compiler keeps and the register it gives the intermediate.

```c
/* one expression */
total = base + offset * stride + bias;

/* split: the product and the first sum are separate values */
scaled = offset * stride;
total = base + scaled;
total += bias;
```

The reverse also works: inline a temporary the original never had, when
the target recomputes a value instead of keeping it in a register.

Floating-point arithmetic is not associative, so regrouping a float
expression changes results; for floats, match the original grouping
exactly rather than steering with it.

## Reorder reads and writes

Symptom: the right loads and stores in a different order, or one load
hoisted above a call or a branch.

Many compilers keep independent memory operations close to source order.
Reorder independent statements to follow the order in the target: read
fields in the order the target loads them, write in the order it stores.

```c
/* target stores y before x */
p->y = ny;
p->x = nx;
```

Only reorder statements that are independent. If two pointers may alias,
or a call in between may read or write the same memory, the order is part
of the behavior.

## Change the branch shape

Symptom: a condition tested with the opposite jump, the fall-through and
the taken block swapped, a missing or extra jump, or a jump table where
the target has a compare chain (or the reverse).

Equivalent shapes that often compile differently:

- `if (!c) { A } else { B }` and `if (c) { B } else { A }`;
- an early `return` and a nested `if`;
- a ternary and an `if`/`else` assignment;
- `for`, `while`, and `do`/`while` for the same loop, including a loop
  guarded by an `if` before a `do`/`while`;
- `switch` and an `if`/`else if` chain; the number and density of `case`
  values can decide whether a jump table is emitted;
- `&&` in one condition and two nested `if` statements.

```c
/* nested */
if (e != NULL) {
    if (e->alive) {
        update(e);
    }
}

/* early exit */
if (e == NULL) {
    return;
}
if (e->alive) {
    update(e);
}
```

## Declaration order and types

Symptom: the right instructions with a different register, or locals at
different stack offsets.

- Declaration order of locals can change stack slot assignment and, with
  some register allocators, the order in which registers are handed out.
  Try the order the target's stack offsets suggest.
- A value the target keeps in a register across a loop may need to be a
  local in the source rather than a repeated field read, and the reverse.
- Types show in the instructions: sign extension versus zero extension
  tells signed from unsigned, and operand width tells `char`, `short`,
  and `int` apart. Change a type only to what the target shows; a type
  change that the target does not show changes behavior on some input.
- Parameter and return types decide the calling sequence at the boundary;
  check them against the original ABI rather than steering them.

## Keep original behavior

The goal is the original program, not a better one. Keep:

- bugs, such as an off-by-one bound or a missing null check;
- behavior the language leaves undefined, written so the pinned compiler
  produces the same code;
- odd constants, redundant work, and dead stores the target contains;
- the original evaluation order of calls with side effects.

Wrong: "Fixed the bound to `< count` while matching `Inventory_Add`." The
function no longer matches, and if it still did by accident, the program
now behaves differently from the original.

Right: match the original exactly. If a fix is wanted, write it in a
separate non-matching build or patch layer, and note the original defect
in a comment in the matching source.

## Grounding

No public primary source documents these techniques as a guide; they are
general practice in matching projects and follow from how optimizing
compilers group expressions, schedule memory operations, lay out blocks,
and allocate registers. Treat each one as a hypothesis for the pinned
compiler: rebuild, diff, and keep only the changes the diff confirms.
