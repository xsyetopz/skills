# Changelog

All notable changes to this project are documented in this file. The format
follows [Keep a Changelog][kac] and the project uses
[Semantic Versioning][semver].

## [Unreleased]

## [1.4.0] - 2026-05-02

### Added

- `Widget.resize()` accepts a `keep_ratio` argument.

### Changed

- `Widget.render()` returns bytes instead of a string.

## [1.3.1] - 2026-03-18

### Fixed

- Widgets with an empty title no longer raise `IndexError`.

[kac]: https://keepachangelog.com/en/1.1.0/
[semver]: https://semver.org/spec/v2.0.0.html
[Unreleased]: https://git.example.invalid/widgetkit/compare/v1.4.0...HEAD
[1.4.0]: https://git.example.invalid/widgetkit/compare/v1.3.1...v1.4.0
[1.3.1]: https://git.example.invalid/widgetkit/releases/tag/v1.3.1
