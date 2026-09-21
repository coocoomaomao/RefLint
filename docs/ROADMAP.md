# Roadmap

## v0.1 — local QA + first online DOI verification

- parsing / structural errors
- duplicate keys and fields
- duplicate DOI / title
- required fields
- DOI syntax
- year sanity
- CLI + CI
- opt-in DOI resolution through doi.org
- CSL-JSON title / year / venue comparison
- explicit timeout and conservative network-failure behavior

## v0.2 — network verification hardening

- cache DOI metadata locally
- registry-aware enrichment where useful
- rate-limit handling
- batch performance improvements
- configurable online verification policy

## v0.3 — publication workflow

- retraction / correction signals from authoritative sources
- sourced publisher / style presets
- GitHub Action annotations
- machine-readable JSON output

## Long term

RefLint can become the reference-QA component of a wider academic-lint toolchain alongside FigureLint and a future manuscript-level PaperLint.
