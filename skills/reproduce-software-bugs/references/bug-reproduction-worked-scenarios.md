# Worked scenarios for Bug Reproduction

## Parser reduction

Original: 40 MB input causes the last empty CSV field to disappear.

1. Freeze parser version/options and expected field count.
1. Reduce rows while checking the same final-field mismatch.
1. Reduce columns and quoting independently.
1. Keep a control input differing by one delimiter that parses correctly.
1. Package the minimal bytes, parser command, expected fields, and actual
   fields.

A missing file or malformed-encoding error is a different failure.

## Race reproduction

```text
thread A: observe generation N
thread B: replace object, generation N+1
thread A: publish result only if generation is still N
```

Use barriers or a controllable scheduler to force the stale-publication window.
A `sleep(1)` can change timing but does not establish the race contract.

## Fresh-run contract

```sh
mkdir /tmp/repro-clean && cd /tmp/repro-clean
cp -R /path/to/repro/. .
<documented setup command>
<documented run command>
```

Record expected target failure and a separate environment sanity result.
