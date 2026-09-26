# Changelog

All notable changes to this project are documented in this file. The format
follows [Keep a Changelog 2.0.0][kac] and the project uses
[Semantic Versioning 2.0.0][semver].

## [Unreleased]

## [1.1.0] - 2026-09-20

### Added

- Cancel a running export with `POST /exports/{id}/cancel`; the previous
  export at the destination is kept.

### Fixed

- Exports no longer leave `.tmp` files behind when validation fails.

## [1.0.1] - 2026-08-02 [YANKED]

### Security

- CVE-2026-00001: path traversal in export destinations. Upgrade to 1.1.0;
  1.0.1 was withdrawn because its fix was incomplete.

## [1.0.0] - 2026-07-15

### Added

- Export reports to CSV.

[kac]: https://keepachangelog.com/en/2.0.0/
[semver]: https://semver.org/spec/v2.0.0.html
[Unreleased]: https://example.invalid/compare/v1.1.0...HEAD
[1.1.0]: https://example.invalid/compare/v1.0.1...v1.1.0
[1.0.1]: https://example.invalid/compare/v1.0.0...v1.0.1
[1.0.0]: https://example.invalid/releases/tag/v1.0.0
