# Changelog

[![CI](https://github.com/monostronomy/find-replace-rename/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/monostronomy/find-replace-rename/actions)

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project adheres (loosely) to Semantic Versioning.

## [0.3.2] - 2025-08-24

### Fixed

- README formatting cleanups and minor typo corrections.
- Updated example JSON timestamp formatting and spacing.

## [0.3.1] - 2025-08-23

### Documentation

- Updated README wording, replaced'dmo' to 'demo' in examples.


## [0.3.0] - 2025-08-23

### Added

- `--find-only` mode to enumerate matches without performing any renames.
- Per-match text and JSONL logging with `action: "find"`, plus summary.

<!-- markdownlint-disable-next-line MD024 -->
### Documentation

- README updated with `--find-only` usage, behavior notes, and examples.

---

## [0.2.0] - 2025-08-23

<!-- markdownlint-disable-next-line MD024 -->
### Added

- `--regex` option for pattern-based find/replace using regular expressions.
- Support capture groups/backreferences in replacement (e.g., `\1`).
- JSONL logs now include a `regex` flag in entries and summary.

### Changed

- Documentation updated with regex section and examples.

---

## [0.1.0] - 2025-08-23

<!-- markdownlint-disable-next-line MD024 -->
### Added

- Initial public release of the recursive file renamer.
- Interactive and CLI modes with confirmation flow (y/n/a/c).
- Case-insensitive matching by default; `--cs` for case-sensitive.
- `--dry-run` preview mode.
- `--include-dirs` to include directories.
- `--ext` to filter by extensions (case-insensitive).
- Approve-each mode and progress indicator.
- Verbose text logging to dated files (collision-safe).
- Structured JSONL logging with `--json-log` (collision-safe).
- `--backup` to create `.bak` copies of originals before rename.
- No-space collision suffixes for rename and backups: `(1)`, `(2)`, ...

### Documentation

- Comprehensive README with examples and Windows 11 PATH instructions.
- Added `MIT LICENSE`
- Added Windows wrapper `file_renamer.cmd` for PATH usage.

### Project

- Added `.gitignore`.
- Added `pyproject.toml` with console entry point `file-renamer`.
