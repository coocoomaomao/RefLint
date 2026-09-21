from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from .checks import check_entries, collect_bib_files
from .models import Severity
from .parser import parse_bibtex

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="Lint academic references before submission.",
)
console = Console()


@app.callback()
def main() -> None:
    """RefLint command group."""


@app.command()
def check(
    target: Path = typer.Argument(
        ...,
        exists=True,
        readable=True,
        help="BibTeX file or directory to inspect.",
    ),
    strict: bool = typer.Option(
        False,
        "--strict",
        help="Exit with code 1 when warnings are present.",
    ),
) -> None:
    """Check one .bib file or every .bib file in a directory."""
    files = collect_bib_files(target)
    if not files:
        console.print("[yellow]No .bib files found.[/yellow]")
        raise typer.Exit(code=0)

    table = Table(title="RefLint")
    table.add_column("File", overflow="fold")
    table.add_column("Entry", no_wrap=True)
    table.add_column("Severity")
    table.add_column("Code", min_width=22, no_wrap=True)
    table.add_column("Message", overflow="fold")

    error_count = 0
    warning_count = 0
    entry_count = 0

    for path in files:
        entries, parse_findings = parse_bibtex(path)
        entry_count += len(entries)
        findings = [*parse_findings, *check_entries(path, entries)]

        if not findings:
            table.add_row(str(path), "—", "pass", "OK", "No findings.")
            continue

        for finding in findings:
            if finding.severity is Severity.ERROR:
                error_count += 1
            elif finding.severity is Severity.WARNING:
                warning_count += 1

            table.add_row(
                str(finding.path),
                finding.entry_key or "—",
                finding.severity.value,
                finding.code,
                finding.message,
            )

    console.print(table)
    console.print(
        f"Checked {len(files)} file(s), {entry_count} reference(s): "
        f"{error_count} error(s), {warning_count} warning(s)."
    )

    if error_count:
        raise typer.Exit(code=2)
    if strict and warning_count:
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
