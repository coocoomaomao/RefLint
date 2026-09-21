from pathlib import Path

from reflint.checks import check_entries, normalize_doi, normalize_title
from reflint.models import ReferenceEntry, Severity


def entry(key: str, entry_type: str = "article", **fields: str) -> ReferenceEntry:
    return ReferenceEntry(key=key, entry_type=entry_type, fields=fields, line=1)


def test_normalize_doi_accepts_url_and_prefix() -> None:
    assert normalize_doi("https://doi.org/10.1234/ABC.1") == "10.1234/abc.1"
    assert normalize_doi("doi: 10.1234/ABC.1") == "10.1234/abc.1"


def test_normalize_title_ignores_braces_case_and_punctuation() -> None:
    assert normalize_title("{A Study}: Of Cats!") == normalize_title("a study of cats")


def test_missing_required_article_fields_warn() -> None:
    findings = check_entries(
        Path("refs.bib"),
        [entry("one", author="A", title="T", year="2024")],
        current_year=2026,
    )
    finding = next(f for f in findings if f.code == "MISSING_REQUIRED_FIELD")
    assert finding.severity is Severity.WARNING
    assert "journal" in finding.message


def test_book_accepts_editor_instead_of_author() -> None:
    findings = check_entries(
        Path("refs.bib"),
        [
            entry(
                "book",
                entry_type="book",
                editor="A Editor",
                title="A Useful Book",
                publisher="Press",
                year="2024",
            )
        ],
        current_year=2026,
    )
    assert not any(f.code == "MISSING_REQUIRED_FIELD" for f in findings)


def test_invalid_doi_warns() -> None:
    findings = check_entries(
        Path("refs.bib"),
        [
            entry(
                "one",
                author="A",
                title="A sufficiently long title",
                journal="J",
                year="2024",
                doi="not-a-doi",
            )
        ],
        current_year=2026,
    )
    assert any(f.code == "DOI_INVALID" for f in findings)


def test_duplicate_doi_warns_after_normalization() -> None:
    fields = dict(author="A", journal="J", year="2024")
    entries = [
        entry("one", title="First paper title", doi="10.1234/ABC.1", **fields),
        entry(
            "two",
            title="Second paper title",
            doi="https://doi.org/10.1234/abc.1",
            **fields,
        ),
    ]
    findings = check_entries(Path("refs.bib"), entries, current_year=2026)
    assert any(f.code == "DUPLICATE_DOI" for f in findings)


def test_duplicate_title_warns_after_normalization() -> None:
    fields = dict(author="A", journal="J", year="2024")
    entries = [
        entry("one", title="{A Study of Scientific Cats}", **fields),
        entry("two", title="A study of scientific cats!", **fields),
    ]
    findings = check_entries(Path("refs.bib"), entries, current_year=2026)
    assert any(f.code == "DUPLICATE_TITLE" for f in findings)


def test_future_year_warns() -> None:
    findings = check_entries(
        Path("refs.bib"),
        [
            entry(
                "one",
                author="A",
                title="A sufficiently long title",
                journal="J",
                year="2030",
            )
        ],
        current_year=2026,
    )
    assert any(f.code == "YEAR_FUTURE" for f in findings)


def test_next_year_is_allowed_for_online_first_records() -> None:
    findings = check_entries(
        Path("refs.bib"),
        [
            entry(
                "one",
                author="A",
                title="A sufficiently long title",
                journal="J",
                year="2027",
            )
        ],
        current_year=2026,
    )
    assert not any(f.code == "YEAR_FUTURE" for f in findings)
