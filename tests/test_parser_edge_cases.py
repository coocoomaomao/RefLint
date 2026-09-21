from pathlib import Path

from reflint.parser import parse_bibtex


def test_duplicate_entry_key_is_structural_error(tmp_path: Path) -> None:
    path = tmp_path / "duplicates.bib"
    path.write_text(
        """@article{samekey,
  author = {First Author},
  title = {First Title},
  journal = {Journal A},
  year = {2024}
}

@book{samekey,
  author = {Second Author},
  title = {Second Title},
  publisher = {Example Press},
  year = {2025}
}
""",
        encoding="utf-8",
    )

    entries, findings = parse_bibtex(path)

    assert len(entries) == 1
    finding = next(f for f in findings if f.code == "DUPLICATE_KEY")
    assert finding.entry_key == "samekey"


def test_duplicate_field_key_is_structural_error(tmp_path: Path) -> None:
    path = tmp_path / "duplicate-fields.bib"
    path.write_text(
        """@article{duplicatefield,
  author = {Miao Cat},
  title = {First Title},
  title = {Second Title},
  journal = {Journal of Cats},
  year = {2026}
}
""",
        encoding="utf-8",
    )

    _entries, findings = parse_bibtex(path)

    finding = next(f for f in findings if f.code == "DUPLICATE_FIELD")
    assert "title" in finding.message.lower()


def test_field_names_are_normalized_to_lowercase(tmp_path: Path) -> None:
    path = tmp_path / "mixed-case.bib"
    path.write_text(
        """@article{mixed,
  AUTHOR = {Miao Cat},
  Title = {Mixed Case Fields},
  JOURNAL = {Journal of Cats},
  Year = {2026},
  DOI = {10.1234/cats.mixed}
}
""",
        encoding="utf-8",
    )

    entries, findings = parse_bibtex(path)

    assert not findings
    assert entries[0].fields["author"] == "Miao Cat"
    assert entries[0].fields["doi"] == "10.1234/cats.mixed"


def test_comments_strings_and_preambles_do_not_become_entries(tmp_path: Path) -> None:
    path = tmp_path / "mixed-blocks.bib"
    path.write_text(
        """@comment{A comment}
@string{joc = "Journal of Cats"}
@preamble{"RefLint fixture"}

@article{cat2026,
  author = {Miao Cat},
  title = {Unicode 猫 Reference},
  journal = joc,
  year = {2026}
}
""",
        encoding="utf-8",
    )

    entries, findings = parse_bibtex(path)

    assert not findings
    assert len(entries) == 1
    assert entries[0].key == "cat2026"
