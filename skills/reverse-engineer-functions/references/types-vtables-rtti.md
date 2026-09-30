# Types, vtables, and RTTI

## Contents

- [Field recovery](#field-recovery)
- [Consistency across xrefs](#consistency-across-xrefs)
- [Field table format](#field-table-format)
- [Itanium C++ ABI](#itanium-c-abi)
- [MSVC RTTI](#msvc-rtti)
- [Map virtual slots to methods](#map-virtual-slots-to-methods)
- [Sources](#sources)

Recover a type from how the code uses memory, then check it against every
place that touches it. Record each field with the address of the access
that shows it.

## Field recovery

1. Pick a base: a register that holds a pointer to the object (an
   argument, the return value of an allocation, or `this`).
1. Follow the base through moves and copies. Each access `[base+off]`
   gives one field candidate at `off`.
1. Take the width from the access (byte, 16-bit, 32-bit, 64-bit, vector).
1. Take the kind from the instruction that uses the value:
   - sign extension or signed compare or divide: signed integer;
   - zero extension or unsigned compare: unsigned integer;
   - floating-point load or arithmetic: float or double;
   - dereference or pass as a pointer argument: pointer (record the target
     type separately);
   - call through it: function pointer, or a vptr if it is at the offset
     loaded before a virtual call.
1. Look for an array: an access `[base+idx*scale+off]`, or a loop that
   steps a pointer by a constant. The scale is the element size.
1. Find the size: an allocation with a constant size followed by a
   constructor call on the result gives the object size for that class.
   A `memset` or copy of a constant length over the object is a second
   check.

Offsets below the highest accessed field that no access touches are
unknown bytes, not padding. Name them `unk_<offset>` and keep them.

## Consistency across xrefs

A field is confirmed when every function that touches it agrees on offset,
width, and kind. For each field:

- List the addresses of all accesses you checked.
- Mark the field "confirmed" only when all agree, "single use" when only
  one access was found, and "conflict" when two disagree.
- For a conflict, list both accesses. Common causes are a union, a
  different type at the same offset in a derived class, or a wrong base
  (the register held a different object at that point). Do not pick one
  silently.

## Field table format

```text
struct Session  /* size 0x48 from alloc at 0x1400123a0, confirmed */
off   size kind      name         conf.     evidence
0x00  8    vptr      vftable      seen      store at 0x1400123c4
0x08  4    uint32    flags        inferred  and/test at 0x140012500
0x0c  4    int32     unk_0c       -         single use 0x140012514
0x10  8    char*     name         inferred  passed to strlen-like loop
                                            at 0x140012530
0x18  48   ?         unk_18       -         no accesses found
```

`conf.` is the name confidence (seen, inferred, guess). Evidence is an
address the user can open.

## Itanium C++ ABI

GCC and Clang use this ABI on most targets other than Windows.

Vtable layout, in order:

1. Virtual call (vcall) offsets, when needed.
1. Virtual base (vbase) offsets, when needed.
1. Offset-to-top: a `ptrdiff_t` displacement from this vptr location to
   the top of the object.
1. Typeinfo pointer.
1. Virtual function pointers.

The vptr (the address point) points at the first function pointer, not at
the start of the table. So a load from `[vptr-8]` on a 64-bit target reads
the typeinfo pointer, and `[vptr-16]` reads offset-to-top.

- A class with no primary base has its vptr at offset 0.
- A virtual destructor takes two slots: the complete-object destructor
  (`D1`) then the deleting destructor (`D0`). The base-object destructor
  (`D2`) is not in the vtable.
- `this` is the first parameter, but a hidden return pointer comes before
  `this`, and so does the VTT parameter when one is passed.
- Symbols: `_ZTV` for vtables, `_ZTI` for typeinfo, `_ZTS` for typeinfo
  name strings.
- Typeinfo classes: `__class_type_info`, `__si_class_type_info` (with
  `__base_type`), and `__vmi_class_type_info` (`__flags`, `__base_count`,
  `__base_info[]`). The typeinfo's own vptr tells you which of these it
  is, and so which shape of inheritance the class has.

## MSVC RTTI

The fields below come from a third-party description of 32-bit layouts.
Confirm the x64 encoding (field widths, and whether pointers are absolute
or image-relative) in the binary before you rely on it.

- `vftable[-1]` holds a pointer to an `RTTICompleteObjectLocator`.
- `RTTICompleteObjectLocator`: signature, offset (of this vtable in the
  complete class), `cdOffset`, `pTypeDescriptor`, `pClassDescriptor`.
- `RTTIClassHierarchyDescriptor`: signature, attributes (bit 0: multiple
  inheritance, bit 1: virtual inheritance), `numBaseClasses`,
  `pBaseClassArray`.
- `RTTIBaseClassDescriptor`: `pTypeDescriptor`, `numContainedBases`,
  `where` (a pointer-to-member displacement), attributes.
- The type descriptor holds the decorated class name. A name read there is
  "seen" evidence.

Destructors in the vftable: the scalar deleting destructor frees memory
when `flags & 1`; the vector deleting destructor uses `0x2` for arrays.
A slot that calls the destructor body and then, under a test of an
argument bit, a free routine, is a deleting destructor.

## Map virtual slots to methods

1. Find the vtable: a constant address stored at the vptr offset in a
   constructor, or the address loaded before a virtual call.
1. Find its start and end. The start is the address point (after the
   typeinfo or locator pointer). The end is where entries stop being code
   addresses, or where the next vtable's metadata begins.
1. Number the slots from 0 at the address point.
1. At each virtual call, the load `[vptr + N * pointer_size]` gives slot
   `N`. Record the call site with the slot.
1. Compare with the vtables of related classes found through RTTI. A slot
   index that holds a different function in a related class suggests an
   override; confirm it from the call sites before naming it.

## Sources

- Itanium C++ ABI, vtable layout and RTTI: [itanium]
- MSVC RTTI structures (third-party, 32-bit layouts): [openrce]

[itanium]: https://itanium-cxx-abi.github.io/cxx-abi/abi.html#vtable
[openrce]: http://www.openrce.org/articles/full_view/23
