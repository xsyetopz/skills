# settings-loading Specification

## Purpose

How config-tool reads `service.ini` into sections of string keys and values.

## Requirements

### Requirement: Inline comments

The loader SHALL ignore everything from the first `#` on a line to the end of that line.

#### Scenario: Comment after a value

- **WHEN** a line reads `host = db.internal   # primary`
- **THEN** the value of `host` is `db.internal`

### Requirement: Duplicate keys

When a key appears twice in one section, the loader SHALL keep the last value.

#### Scenario: Later value wins

- **WHEN** section `[cache]` has `ttl = 30` and then `ttl = 60`
- **THEN** the value of `ttl` is `60`

### Requirement: Key case

The loader SHALL keep the case of each key as written.

#### Scenario: Mixed-case key

- **WHEN** section `[db]` has `Host = db.internal`
- **THEN** the section has the key `Host` and no key `host`
