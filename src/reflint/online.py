from __future__ import annotations

from difflib import SequenceMatcher
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx

from .checks import _DOI_RE, normalize_doi, normalize_title
from .models import Finding, ReferenceEntry, Severity

_CSL_JSON = "application/vnd.citationstyles.csl+json"
_USER_AGENT = "RefLint/0.1.0 (+https://github.com/coocoomaomao/RefLint)"


def _first_text(value: Any) -> str | None:
    if isinstance(value, str):
        return value.strip() or None
    if isinstance(value, list):
        for item in value:
            text = _first_text(item)
            if text:
                return text
    return None


def _metadata_year(data: dict[str, Any]) -> str | None:
    for key in ("issued", "published-print", "published", "created"):
        value = data.get(key)
        if not isinstance(value, dict):
            continue
        parts = value.get("date-parts")
        if (
            isinstance(parts, list)
            and parts
            and isinstance(parts[0], list)
            and parts[0]
        ):
            year = parts[0][0]
            if isinstance(year, int):
                return str(year)
            if isinstance(year, str) and year.isdigit():
                return year
    return None


def _similarity(left: str, right: str) -> float:
    return SequenceMatcher(None, left, right).ratio()


def _short(value: str, limit: int = 120) -> str:
    value = " ".join(value.split())
    return value if len(value) <= limit else value[: limit - 1] + "…"


def verify_doi_metadata(
    path: Path,
    entries: list[ReferenceEntry],
    *,
    timeout: float = 10.0,
    client: httpx.Client | None = None,
) -> list[Finding]:
    """Resolve valid DOI values and compare available CSL-JSON metadata.

    Network failures are informational rather than evidence that a DOI is invalid.
    """
    findings: list[Finding] = []
    owns_client = client is None

    if client is None:
        client = httpx.Client(
            follow_redirects=True,
            timeout=timeout,
            headers={
                "Accept": _CSL_JSON,
                "User-Agent": _USER_AGENT,
            },
        )

    try:
        for entry in entries:
            raw_doi = entry.fields.get("doi", "").strip()
            if not raw_doi:
                continue

            doi = normalize_doi(raw_doi)
            if not _DOI_RE.fullmatch(doi):
                # The local DOI syntax rule reports this already.
                continue

            url = f"https://doi.org/{quote(doi, safe='/')}"

            try:
                response = client.get(
                    url,
                    headers={
                        "Accept": _CSL_JSON,
                        "User-Agent": _USER_AGENT,
                    },
                )
            except httpx.HTTPError as exc:
                findings.append(
                    Finding(
                        path=path,
                        severity=Severity.INFO,
                        code="DOI_LOOKUP_UNAVAILABLE",
                        message=(
                            f"Could not verify DOI {doi} because the resolver request "
                            f"failed: {exc.__class__.__name__}."
                        ),
                        entry_key=entry.key,
                        line=entry.line,
                    )
                )
                continue

            if response.status_code in {404, 410}:
                findings.append(
                    Finding(
                        path=path,
                        severity=Severity.WARNING,
                        code="DOI_NOT_RESOLVED",
                        message=f"DOI did not resolve through doi.org: {doi}.",
                        entry_key=entry.key,
                        line=entry.line,
                    )
                )
                continue

            if response.status_code == 429 or response.status_code >= 500:
                findings.append(
                    Finding(
                        path=path,
                        severity=Severity.INFO,
                        code="DOI_LOOKUP_UNAVAILABLE",
                        message=(
                            f"DOI resolver was temporarily unavailable for {doi} "
                            f"(HTTP {response.status_code})."
                        ),
                        entry_key=entry.key,
                        line=entry.line,
                    )
                )
                continue

            if response.status_code < 200 or response.status_code >= 300:
                findings.append(
                    Finding(
                        path=path,
                        severity=Severity.INFO,
                        code="DOI_LOOKUP_UNAVAILABLE",
                        message=(
                            f"Could not verify DOI {doi}; doi.org returned "
                            f"HTTP {response.status_code}."
                        ),
                        entry_key=entry.key,
                        line=entry.line,
                    )
                )
                continue

            try:
                data = response.json()
            except ValueError:
                findings.append(
                    Finding(
                        path=path,
                        severity=Severity.INFO,
                        code="DOI_METADATA_UNAVAILABLE",
                        message=(
                            f"DOI {doi} resolved, but CSL-JSON metadata could not "
                            "be decoded."
                        ),
                        entry_key=entry.key,
                        line=entry.line,
                    )
                )
                continue

            if not isinstance(data, dict):
                findings.append(
                    Finding(
                        path=path,
                        severity=Severity.INFO,
                        code="DOI_METADATA_UNAVAILABLE",
                        message=f"DOI {doi} resolved, but returned metadata was unexpected.",
                        entry_key=entry.key,
                        line=entry.line,
                    )
                )
                continue

            findings.append(
                Finding(
                    path=path,
                    severity=Severity.INFO,
                    code="DOI_RESOLVED",
                    message=f"DOI resolved successfully: {doi}.",
                    entry_key=entry.key,
                    line=entry.line,
                )
            )

            local_title = entry.fields.get("title", "").strip()
            remote_title = _first_text(data.get("title"))
            if local_title and remote_title:
                left = normalize_title(local_title)
                right = normalize_title(remote_title)
                if left and right and _similarity(left, right) < 0.85:
                    findings.append(
                        Finding(
                            path=path,
                            severity=Severity.WARNING,
                            code="DOI_TITLE_MISMATCH",
                            message=(
                                "BibTeX title differs substantially from DOI metadata. "
                                f"Metadata title: '{_short(remote_title)}'."
                            ),
                            entry_key=entry.key,
                            line=entry.line,
                        )
                    )

            local_year = entry.fields.get("year", "").strip()
            remote_year = _metadata_year(data)
            if (
                local_year.isdigit()
                and len(local_year) == 4
                and remote_year
                and local_year != remote_year
            ):
                findings.append(
                    Finding(
                        path=path,
                        severity=Severity.INFO,
                        code="DOI_YEAR_MISMATCH",
                        message=(
                            f"BibTeX year is {local_year}; DOI metadata reports "
                            f"{remote_year}. Online-first and issue years can differ."
                        ),
                        entry_key=entry.key,
                        line=entry.line,
                    )
                )

            local_container = (
                entry.fields.get("journal", "").strip()
                or entry.fields.get("booktitle", "").strip()
            )
            remote_container = _first_text(data.get("container-title"))
            if local_container and remote_container:
                left = normalize_title(local_container)
                right = normalize_title(remote_container)
                if left and right and _similarity(left, right) < 0.75:
                    findings.append(
                        Finding(
                            path=path,
                            severity=Severity.INFO,
                            code="DOI_CONTAINER_MISMATCH",
                            message=(
                                "BibTeX venue differs from DOI metadata. "
                                f"Metadata venue: '{_short(remote_container)}'."
                            ),
                            entry_key=entry.key,
                            line=entry.line,
                        )
                    )
    finally:
        if owns_client:
            client.close()

    return findings
