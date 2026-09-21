from __future__ import annotations

from pathlib import Path

import bibtexparser

from .models import Finding, ReferenceEntry, Severity


def parse_bibtex(path: Path) -> tuple[list[ReferenceEntry], list[Finding]]:
    """Parse a BibTeX file into RefLint's small internal model."""
    try:
        library = bibtexparser.parse_file(str(path))
    except (OSError, UnicodeError, LookupError, ValueError) as exc:
        return [], [
            Finding(
                path=path,
                severity=Severity.ERROR,
                code="BIB_UNREADABLE",
                message=f"BibTeX file could not be parsed: {exc}",
            )
        ]

    findings: list[Finding] = []

    for block in library.blocks:
        kind = type(block).__name__
        line = getattr(block, "start_line", None)

        if kind == "DuplicateBlockKeyBlock":
            key = getattr(block, "key", None)
            findings.append(
                Finding(
                    path=path,
                    severity=Severity.ERROR,
                    code="DUPLICATE_KEY",
                    message=f"Duplicate BibTeX key detected: {key or 'unknown'}.",
                    entry_key=key,
                    line=line,
                )
            )
        elif kind == "DuplicateFieldKeyBlock":
            keys = sorted(getattr(block, "duplicate_keys", set()))
            entry = getattr(block, "entry", None)
            entry_key = getattr(entry, "key", None)
            findings.append(
                Finding(
                    path=path,
                    severity=Severity.ERROR,
                    code="DUPLICATE_FIELD",
                    message=(
                        "Duplicate field name(s) detected: "
                        + (", ".join(keys) if keys else "unknown")
                        + "."
                    ),
                    entry_key=entry_key,
                    line=line,
                )
            )
        elif "ParsingFailed" in kind:
            error = getattr(block, "error", None)
            findings.append(
                Finding(
                    path=path,
                    severity=Severity.ERROR,
                    code="BIB_PARSE_ERROR",
                    message=f"A BibTeX block could not be parsed: {error or kind}.",
                    line=line,
                )
            )

    entries: list[ReferenceEntry] = []
    for entry in library.entries:
        fields = {
            str(key).lower(): str(field.value).strip()
            for key, field in entry.fields_dict.items()
        }
        entries.append(
            ReferenceEntry(
                key=str(entry.key),
                entry_type=str(entry.entry_type).lower(),
                fields=fields,
                line=getattr(entry, "start_line", None),
            )
        )

    return entries, findings
