# Worked requirement examples

## Async export with cancellation

Requirement:

> When an authorized user starts an export, the service creates one export job
> for the normalized request and returns its stable job identifier. A
> cancellation request made before publication prevents further output
> publication and leaves no downloadable partial artifact. Cancellation after
> publication reports that the completed artifact already exists and does not
> delete it.

Acceptance criteria observe job identity, authorization, state transitions,
partial artifact absence, and post-publication behavior. They do not require a
specific queue, class name, or database.

## File replacement policy is unresolved

Request: “Import this configuration file.” Existing code sometimes overwrites
and sometimes rejects duplicates. Do not choose silently. Present policies:

1. reject duplicate identity with a documented conflict;
1. replace atomically and retain rollback/audit state;
1. create a new version while preserving prior versions.

The selected policy becomes a requirement only after the user or authoritative
contract decides it.

## Bad acceptance criterion

> `ConfigImporter` calls `parseV2()` exactly once.

This freezes an implementation. A behavior criterion instead supplies a valid v2
document, observes the resulting configuration and warnings, and includes an
invalid document whose state remains unchanged.
