# Roadmap

## v0.1 — local deterministic BibTeX QA

- parsing / structural errors
- duplicate keys and fields
- duplicate DOI / title
- required fields
- DOI syntax
- year sanity
- CLI + CI

## v0.2 — network verification

- resolve DOI values
- compare title / year / venue metadata against authoritative APIs
- cache results locally
- explicit offline mode
- rate-limit and timeout behavior

## v0.3 — publication workflow

- retraction / correction signals from authoritative sources
- sourced publisher / style presets
- GitHub Action annotations
- machine-readable JSON output

## Long term

RefLint can become the reference-QA component of a wider academic-lint toolchain alongside FigureLint and a future manuscript-level PaperLint.
