# Changelog

All notable changes to RefLint will be documented in this file.

## [Unreleased]

### Planned
- cached online verification
- richer registry-specific metadata enrichment
- retraction / correction signals
- JSON output
- GitHub Actions annotations

## [0.1.0] - 2026-09-21

### Added
- initial RefLint CLI
- BibTeX parsing through bibtexparser v2
- duplicate DOI and normalized-title checks
- missing-field checks for common BibTeX entry types
- DOI syntax checks
- year format / future-year checks
- duplicate key / field parse findings
- recursive `.bib` scanning
- strict mode and CI-ready exit codes
- explicit `--online` DOI resolution through doi.org
- CSL-JSON title, year, and venue metadata comparison
- conservative network-failure handling
- example good / bad reference libraries
- Python 3.10–3.12 CI

[Unreleased]: https://github.com/coocoomaomao/RefLint/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/coocoomaomao/RefLint/releases/tag/v0.1.0
