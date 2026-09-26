# Export cancellation

Worked specification in the format `scripts/check_requirements.py`
checks. The system is a single-process export service that writes to a
temporary file and publishes by renaming it over the destination on the
same filesystem. The reference implementation and acceptance tests are
`export_cancel.py` and `test_export_cancel.py` in this directory.

## Glossary

- **Job**: one export request, identified by a job ID.
- **Temporary file**: the file a job writes before publication; owned by
  that job only.
- **Destination**: the path the caller named; may already hold a previous
  export.
- **Publication**: the atomic rename of the temporary file onto the
  destination. Its start is the job's linearization point for
  cancellation.
- **Cancel accepted**: the service changed the job's state to cancelled.
  Distinct from a cancel request arriving.

## States

| State | Event | Next state | Observable effect |
| --- | --- | --- | --- |
| writing | cancel accepted | cancelled | temporary file removed; destination unchanged |
| writing | validation fails | failed | temporary file removed; error reported |
| writing | write completes | publishing | none |
| publishing | cancel requested | publishing | cancel reports "publication started" |
| publishing | rename completes | published | destination holds new bytes |
| published | cancel requested | published | outcome stays published |
| cancelled | cancel requested | cancelled | no new effects |

## Requirements

- REQ-EXP-001 [source: issue 42] When a cancel request arrives while a
  job is writing, the export service shall change the job to cancelled
  and remove the job's temporary file.
- REQ-EXP-002 [source: issue 42] When a job is cancelled, the export
  service shall leave the destination's previous contents unchanged.
- REQ-EXP-003 [source: design review 2026-09-01] When a cancel request
  arrives after publication has started, the export service shall report
  that publication has started and keep the job's outcome unchanged.
- REQ-EXP-004 [source: issue 42] While a job is cancelled or published,
  the export service shall treat a repeated cancel request as a no-op
  that returns the current outcome.
- REQ-EXP-005 [source: issue 57] If validation of the export fails, then
  the export service shall remove the job's temporary file and report the
  validation error without publishing.

## Acceptance criteria

- AC-EXP-001 verifies REQ-EXP-001, REQ-EXP-002: Given a destination with
  previous bytes and a job held at a barrier before publication, when a
  cancel is accepted and the writer is released, then the job is
  cancelled, its temporary file is absent, and the destination holds the
  previous bytes.
- AC-EXP-002 verifies REQ-EXP-003: Given a job whose publication has
  started, when a cancel request arrives, then the response says
  publication started and the job ends published with the new bytes.
- AC-EXP-003 verifies REQ-EXP-004: Given a cancelled job and a published
  job, when cancel is requested again on each, then each returns its
  existing outcome and nothing on disk changes.
- AC-EXP-004 verifies REQ-EXP-005: Given export content that fails
  validation, when the job runs, then the job is failed, the error names
  the validation rule, no temporary file remains, and the destination is
  unchanged.

## Open decisions

- DEC-EXP-001: Crash recovery of in-flight jobs is not specified; an
  atomic rename alone does not make publication durable across power
  loss.
- DEC-EXP-002: Cross-filesystem destinations are out of scope; rename is
  not atomic across filesystems.
