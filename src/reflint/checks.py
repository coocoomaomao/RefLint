from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from pathlib import Path
import re
import unicodedata

from .models import Finding, ReferenceEntry, Severity

_DOI_RE = re.compile(r"^10\.\d{4,9}/[-._;()/:A-Z0-9]+$", re.IGNORECASE)
_DOI_PREFIX_RE = re.compile(
    r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)",
    re.IGNORECASE,
)
_LATEX_COMMAND_RE = re.compile(r"\\[A-Za-z]+\*?(?:\[[^\]]*\])?")
_NON_WORD_RE = re.compile(r"[^\w]+", re.UNICODE)

_REQUIRED_FIELDS: dict[str, tuple[str, ...]] = {
    "article": ("author", "title", "journal", "year"),
    "inproceedings": ("author", "title", "booktitle", "year"),
    "incollection": ("author", "title", "booktitle", "publisher", "year"),
    "mastersthesis": ("author", "title", "school", "year"),
    "phdthesis": ("author", "title", "school", "year"),
    "techreport": ("author", "title", "institution", "year"),
    "unpublished": ("author", "title", "note"),
    "proceedings": ("title", "year"),
    "booklet": ("title",),
    "manual": ("title",),
}


def collect_bib_files(target: Path) -> list[Path]:
    if target.is_file():
        return [target] if target.suffix.lower() == ".bib" else []
    return sorted(path for path in target.rglob("*.bib") if path.is_file())


def normalize_doi(value: str) -> str:
    cleaned = value.strip().strip("{}\"")
    cleaned = _DOI_PREFIX_RE.sub("", cleaned)
    return cleaned.strip().lower()


def normalize_title(value: str) -> str:
    text = unicodedata.normalize("NFKC", value)
    text = text.replace("{", "").replace("}", "")
    text = _LATEX_COMMAND_RE.sub("", text)
    text = _NON_WORD_RE.sub(" ", text.casefold())
    return " ".join(text.split())


def _missing_required_fields(entry: ReferenceEntry) -> list[str]:
    required = _REQUIRED_FIELDS.get(entry.entry_type, ())
    missing = [name for name in required if not entry.fields.get(name, "").strip()]

    if entry.entry_type in {"book", "inbook"}:
        if not entry.fields.get("author", "").strip() and not entry.fields.get(
            "editor", ""
        ).strip():
            missing.append("author/editor")

        for name in ("title", "publisher", "year"):
            if not entry.fields.get(name, "").strip():
                missing.append(name)

    if entry.entry_type == "inbook":
        if not entry.fields.get("chapter", "").strip() and not entry.fields.get(
            "pages", ""
        ).strip():
            missing.append("chapter/pages")

    return missing


def check_entries(
    path: Path,
    entries: list[ReferenceEntry],
    *,
    current_year: int | None = None,
) -> list[Finding]:
    """Run deterministic reference checks over parsed BibTeX entries."""
    if current_year is None:
        current_year = datetime.now().year

    findings: list[Finding] = []
    doi_entries: dict[str, list[ReferenceEntry]] = defaultdict(list)
    title_entries: dict[str, list[ReferenceEntry]] = defaultdict(list)

    for entry in entries:
        for field_name, value in entry.fields.items():
            if not value.strip():
                findings.append(
                    Finding(
                        path=path,
                        severity=Severity.WARNING,
                        code="EMPTY_FIELD",
                        message=f"Field '{field_name}' is present but empty.",
                        entry_key=entry.key,
                        line=entry.line,
                    )
                )

        missing = _missing_required_fields(entry)
        if missing:
            findings.append(
                Finding(
                    path=path,
                    severity=Severity.WARNING,
                    code="MISSING_REQUIRED_FIELD",
                    message=(
                        f"@{entry.entry_type} entry is missing required field(s): "
                        + ", ".join(missing)
                        + "."
                    ),
                    entry_key=entry.key,
                    line=entry.line,
                )
            )

        doi = entry.fields.get("doi", "").strip()
        if doi:
            normalized_doi = normalize_doi(doi)
            if not _DOI_RE.fullmatch(normalized_doi):
                findings.append(
                    Finding(
                        path=path,
                        severity=Severity.WARNING,
                        code="DOI_INVALID",
                        message=f"DOI has an unexpected format: {doi}.",
                        entry_key=entry.key,
                        line=entry.line,
                    )
                )
            else:
                doi_entries[normalized_doi].append(entry)

        year = entry.fields.get("year", "").strip()
        if year:
            if not re.fullmatch(r"\d{4}", year):
                findings.append(
                    Finding(
                        path=path,
                        severity=Severity.WARNING,
                        code="YEAR_INVALID",
                        message=f"Year should normally be four digits; found '{year}'.",
                        entry_key=entry.key,
                        line=entry.line,
                    )
                )
            elif int(year) > current_year + 1:
                findings.append(
                    Finding(
                        path=path,
                        severity=Severity.WARNING,
                        code="YEAR_FUTURE",
                        message=(
                            f"Year {year} is more than one year in the future "
                            f"relative to {current_year}."
                        ),
                        entry_key=entry.key,
                        line=entry.line,
                    )
                )

        title = entry.fields.get("title", "").strip()
        if title:
            normalized_title = normalize_title(title)
            if len(normalized_title) >= 10:
                title_entries[normalized_title].append(entry)

    for doi, matches in sorted(doi_entries.items()):
        if len(matches) < 2:
            continue
        keys = ", ".join(entry.key for entry in matches)
        findings.append(
            Finding(
                path=path,
                severity=Severity.WARNING,
                code="DUPLICATE_DOI",
                message=f"The same DOI appears in multiple entries ({keys}): {doi}.",
            )
        )

    for title, matches in sorted(title_entries.items()):
        if len(matches) < 2:
            continue
        keys = ", ".join(entry.key for entry in matches)
        findings.append(
            Finding(
                path=path,
                severity=Severity.WARNING,
                code="DUPLICATE_TITLE",
                message=f"The same normalized title appears in multiple entries: {keys}.",
            )
        )

    return findings
