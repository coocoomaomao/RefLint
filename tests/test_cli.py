from pathlib import Path

from typer.testing import CliRunner

from reflint.cli import app


runner = CliRunner()


def test_help_lists_check_command() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "check" in result.stdout


def test_check_subcommand_accepts_bibtex_path(tmp_path: Path) -> None:
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

    result = runner.invoke(app, ["check", str(path)])

    assert result.exit_code == 0
    assert "1 reference(s)" in result.stdout


def test_online_option_is_explicit_and_supported(tmp_path: Path, monkeypatch) -> None:
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

    called = []

    def fake_verify(path_arg, entries_arg, *, timeout):
        called.append((path_arg, len(entries_arg), timeout))
        return []

    monkeypatch.setattr("reflint.cli.verify_doi_metadata", fake_verify)

    result = runner.invoke(app, ["check", str(path), "--online", "--timeout", "2.5"])

    assert result.exit_code == 0
    assert called == [(path, 1, 2.5)]
