from pathlib import Path

import pytest

pytest.importorskip("bibtexparser")

from reflint.parser import parse_bibtex


def test_parser_reads_basic_entry(tmp_path: Path) -> None:
    path = tmp_path / "refs.bib"
    path.write_text(
        """@article{cat2026,
  author = {Miao Cat},
  title = {A Study of Scientific Cats},
  journal = {Journal of Cats},
  year = {2026},
  doi = {10.1234/cats.2026}
}
""",
        encoding="utf-8",
    )

    entries, findings = parse_bibtex(path)

    assert not findings
    assert len(entries) == 1
    assert entries[0].key == "cat2026"
    assert entries[0].fields["doi"] == "10.1234/cats.2026"
