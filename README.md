# RefLint 🐈‍⬛📚

> **ESLint for academic references.**

**RefLint** is an open-source linter for academic reference libraries. It helps researchers catch deterministic BibTeX quality problems before submission.

Part of **喵造实验室 / MeowBuild Lab**.

## Why

Reference lists accumulate small problems surprisingly easily: duplicated papers, malformed DOI values, incomplete BibTeX entries, suspicious years, or duplicate citation keys.

RefLint turns local reference QA into one command, with optional DOI resolution and metadata verification when you explicitly enable network access.

## MVP checks

- malformed / unreadable BibTeX blocks
- duplicate BibTeX keys
- duplicate field names
- duplicate DOI values after normalization
- duplicate titles after conservative normalization
- missing required fields for common BibTeX entry types
- empty fields
- malformed DOI syntax
- non-four-digit years
- implausibly far-future years
- recursive `.bib` folder scanning
- CI-friendly exit codes and strict mode
- optional DOI resolution through doi.org
- optional CSL-JSON metadata comparison for title, year, and journal / venue
- conservative network-failure handling so an outage is not misreported as a fake DOI

## DOI verification

Local checks are the default. To verify DOI resolution and compare available metadata, opt in with:

~~~bash
reflint check references.bib --online
~~~

Typical online findings include:

~~~text
info     DOI_RESOLVED
warning  DOI_NOT_RESOLVED
warning  DOI_TITLE_MISMATCH
info     DOI_YEAR_MISMATCH
info     DOI_CONTAINER_MISMATCH
info     DOI_LOOKUP_UNAVAILABLE
~~~

A network failure is **not** treated as evidence that a DOI does not exist. RefLint reports lookup outages separately.

The online verifier requests CSL-JSON metadata through the DOI resolver, which routes content-negotiated requests to the DOI registration infrastructure.

## Install from source

Requires Python 3.10+.

~~~bash
git clone https://github.com/coocoomaomao/RefLint.git
cd RefLint
python -m venv .venv
pip install -e .
~~~

For development:

~~~bash
pip install -e ".[dev]"
pytest
~~~

## Usage

Check one BibTeX file:

~~~bash
reflint check references.bib
~~~

Check a folder recursively:

~~~bash
reflint check paper/
~~~

Fail CI when warnings exist:

~~~bash
reflint check references.bib --strict
~~~

Combine strict mode with online DOI verification:

~~~bash
reflint check references.bib --online --strict
~~~

## Example

~~~text
RefLint

references.bib  smithCopy       warning  DUPLICATE_DOI
references.bib  —               warning  DUPLICATE_TITLE
references.bib  missingJournal  warning  MISSING_REQUIRED_FIELD
references.bib  missingJournal  warning  DOI_INVALID
references.bib  missingJournal  warning  YEAR_INVALID
~~~

Try the deliberately problematic fixture:

~~~bash
reflint check examples/bad-references.bib
~~~

## Exit codes

- `0`: no errors; warnings are allowed unless `--strict` is used
- `1`: warnings found in strict mode
- `2`: one or more parsing/structural errors were found

## Philosophy

RefLint should distinguish between:

1. **deterministic local checks** — safe to run without a network,
2. **network-verified facts** — DOI resolution, bibliographic metadata, retractions/corrections,
3. **style rules** — publisher or citation-style-specific requirements.

The tool should not silently turn assumptions into facts.

## Planned next

- caching and rate-limit handling for online verification
- optional richer Crossref / DataCite metadata enrichment
- retraction / correction warnings from authoritative sources
- CSL / journal-style presets where rules can be sourced clearly
- GitHub Actions annotations
- JSON output for editors and other tools

## Release

RefLint v0.1.0 is being prepared for its first public release.

- [v0.1.0 release notes](docs/releases/v0.1.0.md)
- [Publishing guide](docs/PUBLISHING.md)

## License

MIT
