# Changelog

All notable changes to this project are documented in this file. The format
follows [Keep a Changelog][kac] and the project uses
[Semantic Versioning][semver].

## [Unreleased]

### Changed

- Refactored the export pipeline into separate read, transform, and write
  stages.
- Bumped pytest to 8.3.

### Fixed

- Exports now default to UTF-8 instead of the operating system's encoding.
- Exporting to a directory that does not exist no longer crashes; the
  directory is created.

## [0.9.0] - 2026-08-30

### Added

- Export to JSON Lines with `--format jsonl`.

[kac]: https://keepachangelog.com/en/1.1.0/
[semver]: https://semver.org/spec/v2.0.0.html
[Unreleased]: https://git.example.invalid/exporter/compare/v0.9.0...HEAD
[0.9.0]: https://git.example.invalid/exporter/releases/tag/v0.9.0
